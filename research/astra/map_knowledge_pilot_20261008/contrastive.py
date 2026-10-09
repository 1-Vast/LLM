"""Small attribute-alignment pretraining test, not the full published MAP model."""
import ast
import csv
import json
import time

import numpy as np
import torch
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.feature_extraction.text import HashingVectorizer
from threadpoolctl import threadpool_limits

import run as pilot


def alignment_loss(a, b):
    a, b = torch.nn.functional.normalize(a, dim=1), torch.nn.functional.normalize(b, dim=1)
    scores = a @ b.T / .1
    labels = torch.arange(len(a))
    return .5*(torch.nn.functional.cross_entropy(scores,labels) +
               torch.nn.functional.cross_entropy(scores.T,labels))


def main():
    start = time.perf_counter()
    p = json.loads((pilot.HERE/'CONTRASTIVE_PROTOCOL.json').read_text())
    assert pilot.sha(pilot.HERE/'CONTRASTIVE_PROTOCOL.json') == json.loads(
        (pilot.HERE/'CONTRASTIVE_FREEZE.json').read_text())['protocol_sha256']
    labels = json.loads((pilot.PACKET/'PACKET_MANIFEST.json').read_text())['labels']
    exclude = {ast.literal_eval(x)[0][0].strip().casefold() for x in labels}
    rows = list(csv.DictReader((pilot.ROOT/'outputs/paper_01286/map_drugs.csv').open(encoding='utf-8-sig')))
    rows.sort(key=lambda r: pilot.hashlib.sha256(r['smiles'].encode()).hexdigest())
    fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=256)
    hasher = HashingVectorizer(n_features=128, alternate_sign=True, norm='l2')
    RDLogger.DisableLog('rdApp.error')
    selected, seen = [], set()
    def fingerprint(mol):
        bits = np.zeros(256, dtype=np.float32)
        DataStructs.ConvertToNumpyArray(fpgen.GetFingerprint(mol),bits)
        return bits
    for row in rows:
        if not row['moa'].strip() or row['Drug Name'].strip().casefold() in exclude: continue
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is None: continue
        canonical = Chem.MolToSmiles(mol)
        if canonical in seen: continue
        seen.add(canonical); selected.append((row, fingerprint(mol)))
        if len(selected)==2048: break
    assert len(selected)>512
    torch.manual_seed(20261008); torch.set_num_threads(1)
    mol_encoder, text_encoder = torch.nn.Linear(256,24), torch.nn.Linear(128,24)
    opt = torch.optim.Adam(list(mol_encoder.parameters())+list(text_encoder.parameters()),lr=.003)
    x = torch.tensor(np.array([v for _,v in selected]))
    t = torch.tensor(hasher.transform([r['moa'] for r,_ in selected]).toarray(),dtype=torch.float32)
    ntrain = len(selected)-256
    with torch.no_grad(): before=float(alignment_loss(mol_encoder(x[-256:]),text_encoder(t[-256:])))
    trajectory=[]
    for epoch in range(25):
        indices=torch.randperm(ntrain); losses=[]
        for batch in indices.split(128):
            opt.zero_grad();loss=alignment_loss(mol_encoder(x[batch]),text_encoder(t[batch]));loss.backward();opt.step()
            losses.append(float(loss.detach()))
        trajectory.append(float(np.mean(losses)))
    with torch.no_grad():
        after=float(alignment_loss(mol_encoder(x[-256:]),text_encoder(t[-256:])))
        # Attribute retrieval is diagnostic, not biological validity.
        a=torch.nn.functional.normalize(mol_encoder(x[-256:]),dim=1)
        b=torch.nn.functional.normalize(text_encoder(t[-256:]),dim=1)
        retrieval=float((torch.argmax(a@b.T,dim=1)==torch.arange(256)).float().mean())
    e, perm, matched=pilot.representations(labels)
    qualified=json.loads((pilot.HERE/'QUALIFIED_KNOWLEDGE.json').read_text())['records']
    by_name={r['drug']:r for r in qualified}
    names=[ast.literal_eval(label)[0][0].strip().casefold() for label in labels]
    frozen_structure=np.zeros((len(labels),24)); trained=np.zeros((len(labels),24))
    random=np.random.default_rng(20261008).normal(size=(256,24))/np.sqrt(256)
    for i,name in enumerate(names):
        if name not in by_name: continue
        bits=fingerprint(Chem.MolFromSmiles(by_name[name]['smiles']))
        frozen_structure[i]=bits@random
        with torch.no_grad(): trained[i]=torch.nn.functional.normalize(mol_encoder(torch.tensor(bits)[None]),dim=1).numpy()[0]
    unique=sorted(by_name);rng=np.random.default_rng(20261008)
    vectors={name:trained[names.index(name)] for name in unique}
    shuffled=dict(zip(unique,rng.permutation([vectors[n] for n in unique])))
    permtrained=np.array([shuffled.get(n,np.zeros(24)) for n in names])
    np.savez_compressed(pilot.HERE/'CONTRASTIVE_WEIGHTS.npz',
        mol_weight=mol_encoder.weight.detach().numpy(),mol_bias=mol_encoder.bias.detach().numpy(),
        text_weight=text_encoder.weight.detach().numpy(),text_bias=text_encoder.bias.detach().numpy())
    pilot.write('PRETRAINING.json',dict(training_entities=ntrain,heldout_entities=256,
        selected_ids=[r['PubChem ID'] for r,_ in selected],excluded_menu_names=sorted(exclude),
        heldout_InfoNCE_before=before,heldout_InfoNCE_after=after,heldout_retrieval_top1=retrieval,
        chance=1/256,training_losses=trajectory))
    arrays=dict(np.load(pilot.PACKET/'training_arrays.npz'))
    prior=dict(np.load(pilot.PACKET/'public_prior.npz'))
    worlds={'structure24':frozen_structure,'randomknowledge24':e,
            'contrastive24':trained,'contrastive_permuted24':permtrained}
    target_predictions, choices={},{}
    for arm,embedding in worlds.items():
        alpha,losses=pilot.choose(arrays,list(range(45)),embedding,matched,'knowledge')
        choices[arm]=dict(alpha=alpha,inner_losses=losses)
        xs,ys,ps,_,masks=pilot.fold_data(arrays,list(range(45)),0)
        for context,file in json.loads((pilot.PACKET/'PACKET_MANIFEST.json').read_text())['contexts'].items():
            key=context.replace('-','_').replace('/','_');base=prior[key+'__M2']
            obs=np.load(pilot.ROOT/'data/external/tahoe_zeroshot_20261007/observations'/f'{file}.npz')
            basal=np.average(obs['basal_mean'],axis=0,weights=obs['basal_n'])
            f=pilot.feature_rows(np.concatenate([xs[:45],prior[key+'__features'][None]]),
                np.concatenate([arrays['basal'],basal[None]]),embedding,matched,'knowledge')
            correction=pilot.ridge_predict(f[:-1],ys[:45]-ps[:45],masks[:45]&matched,f[-1],alpha)
            target_predictions[key+'__'+arm]=base+np.where(matched,correction,0)
    pilot.write('CONTRASTIVE_CHOICES.json',choices)
    np.savez_compressed(pilot.HERE/'CONTRASTIVE_PREDICTIONS.npz',**target_predictions)
    evaluator=dict(np.load(pilot.PACKET/'evaluator_private.npz'))
    results=[]
    for name,prediction in target_predictions.items():
        key,arm=name.split('__')
        results.append(dict(context=key,arm=arm,**pilot.metrics(prediction,evaluator[key+'__B'],np.ones(146,bool)),
            kg=pilot.kg_replay(prediction,prior['cov'],prior['obsvar'],prior['offset'],evaluator[key+'__A'],evaluator[key+'__B'])))
    pilot.write('CONTRASTIVE_RESULTS.json',results)
    summary={}
    for arm in worlds:
        rows=[r for r in results if r['arm']==arm]
        summary[arm]=dict(alpha=choices[arm]['alpha'],mean_mse=float(np.mean([r['mse'] for r in rows])),
             mean_top5_B=float(np.mean([r['top5_B'] for r in rows])),mean_KG_B=float(np.mean([r['kg']['terminal_B'] for r in rows])))
    pilot.write('CONTRASTIVE_SUMMARY.json',dict(arms=summary,seconds=time.perf_counter()-start,
         source_sha256=pilot.sha(pilot.HERE/'contrastive.py'),status=p['status']))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=1): main()
