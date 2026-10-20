"""Bounded encoder adaptation from human preferences, never synthetic taste labels."""
import json, time
import numpy as np
import torch
import torch.nn.functional as F
from . import store,media
from .inference import Engine

def enable_small_subset(model):
    for p in model.parameters():p.requires_grad_(False)
    selected={n:p for n,p in model.named_parameters() if 'encoder.layer.11.norm' in n}
    if not selected:raise RuntimeError('Expected DINOv2 final-block normalization tensors')
    for p in selected.values():p.requires_grad_(True)
    return selected

def validate_split(rows,split):
    for row in rows:
        ids=[row['edit']['a'],row['left']['b'],row['right']['b']]
        groups={split[store.asset(i)['family']] for i in ids}
        if len(groups)!=1:raise ValueError('Preference crosses source-family splits')
        if row.get('split') not in groups:raise ValueError('Label split does not match registered source families')

def fine_tune(progress=lambda p:None):
    split_path=store.DATA/'evaluation-splits.json'
    if not split_path.exists():raise ValueError('Prepare a source-separated review study first')
    split=json.loads(split_path.read_text())
    with store.connect() as db:rows=[json.loads(r['body']) for r in db.execute('SELECT body FROM labels')]
    rows=[r for r in rows if r['kind']=='preference' and r.get('value') in ('left','right')]
    validate_split(rows,split)
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
    if len(train)<6 or len(val)<2:raise ValueError('Need at least 6 decisive training preferences and 2 validation preferences from separate source families')
    torch.manual_seed(17);engine=Engine();selected=enable_small_subset(engine.model)
    initial={n:p.detach().clone() for n,p in selected.items()}
    optimizer=torch.optim.AdamW(selected.values(),lr=2e-4,weight_decay=.01)
    def tensors(row):
        winner=row[row['value']];loser=row['right' if row['value']=='left' else 'left']
        a=store.asset(row['edit']['a'])
        # Pairwise comparisons share the same outgoing frame by construction.
        if winner['ai']!=loser['ai']:raise ValueError('Training comparisons must share an outgoing cut')
        return engine.tensor([media.frames(a,[winner['ai']])[0],media.frames(store.asset(winner['b']),[winner['bi']])[0],media.frames(store.asset(loser['b']),[loser['bi']])[0]])
    train_x=[tensors(r) for r in train];val_x=[tensors(r) for r in val]
    def loss(x):
        g,s=engine.features_tensor(x);v=F.normalize(torch.cat((g*.65,s*.75),dim=1),dim=1)
        return F.softplus((v[0]@v[2]-v[0]@v[1])*8)
    def evaluate():
        with torch.no_grad():return float(torch.stack([loss(x) for x in val_x]).mean().cpu())
    baseline=evaluate();best=baseline;best_state=None;history=[];start=time.perf_counter()
    for epoch in range(20):
        losses=[]
        for x in train_x:
            optimizer.zero_grad();l=loss(x)+.1*sum((p-initial[n]).square().mean() for n,p in selected.items())
            l.backward();torch.nn.utils.clip_grad_norm_(list(selected.values()),1);optimizer.step();losses.append(float(l.detach().cpu()))
        v=evaluate();history.append(dict(epoch=epoch,train_loss=float(np.mean(losses)),validation_loss=v));progress((epoch+1)/20)
        if v<best:best=v;best_state={n:p.detach().cpu().clone() for n,p in selected.items()}
    # Always preserve the final experimental weights for audit; do not promote a loser.
    state=best_state or {n:p.detach().cpu().clone() for n,p in selected.items()}
    checkpoint=store.DATA/'models'/'adapted-normalization.pt';torch.save(state,checkpoint)
    changed=sum(int(torch.count_nonzero(state[n]-initial[n].cpu())) for n in state)
    report=dict(train_pairs=len(train),validation_pairs=len(val),trainable_parameters=sum(p.numel() for p in selected.values()),
                tensors=list(selected),changed_values=changed,baseline_validation_loss=baseline,best_validation_loss=best,
                improved_validation=best_state is not None,seconds=time.perf_counter()-start,history=history,
                checkpoint=str(checkpoint),heldout_test='Not evaluated; no claim of perceptual improvement')
    (store.DATA/'adaptation-report.json').write_text(json.dumps(report,indent=2));return report
