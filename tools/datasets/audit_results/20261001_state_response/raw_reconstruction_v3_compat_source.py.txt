"""Process-local compatibility for official explicit-head-dimension checkpoint."""
import argparse
from pathlib import Path
import sys

import torch
from transformers import LlamaConfig

from tools.datasets.state_prospective_input import digest, worker, write_json


def run(argv):
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--checkpoint',required=True)
    parser.add_argument('--output',required=True)
    args,_=parser.parse_known_args(argv)
    checkpoint=torch.load(args.checkpoint,map_location='cpu',weights_only=False)
    hp=checkpoint['hyper_parameters']['transformer_backbone_kwargs']
    expected=(328,12,12,64)
    actual=tuple(hp[k] for k in ['hidden_size','num_attention_heads','num_key_value_heads','head_dim'])
    if actual!=expected:raise ValueError('compatibility adapter only supports audited official geometry')
    for layer in range(8):
        for key,shape in [('q_proj',(768,328)),('k_proj',(768,328)),('v_proj',(768,328)),('o_proj',(328,768))]:
            tensor=checkpoint['state_dict'][f'transformer_backbone.layers.{layer}.self_attn.{key}.weight']
            if tuple(tensor.shape)!=shape:raise ValueError('checkpoint attention geometry mismatch')
    del checkpoint
    original=LlamaConfig.validate_architecture

    def explicit_head_validation(self):
        if (self.hidden_size,self.num_attention_heads,self.num_key_value_heads,self.head_dim)==expected:
            # Official stored q/k/v widths are 12*64=768 while hidden width is328.
            # Current attention uses explicit head_dim; the newer divisibility
            # validator assumes implicit head_dim and rejects this older release.
            return
        return original(self)

    LlamaConfig.validate_architecture=explicit_head_validation
    original_validators=LlamaConfig.__class_validators__
    LlamaConfig.__class_validators__=[explicit_head_validation if v is original else v for v in original_validators]
    checked=LlamaConfig(hidden_size=328,num_attention_heads=12,num_key_value_heads=12,head_dim=64)
    if checked.hidden_size!=328 or checked.head_dim!=64:
        raise ValueError('compatibility validation changed dimensions')
    write_json(Path(args.output).parent/'compatibility.json',{
        'checkpoint_sha256':digest(args.checkpoint),'expected_geometry':expected,
        'tensor_shapes_checked_layers':8,'weights_modified':False,'strict_checkpoint_loading':True,
        'patch':'process-local validation permits this exact independently audited explicit head_dim configuration only',
        'upstream_evidence':'transformers v4.55.0 configuration_llama.py accepts explicit head_dim; current LlamaAttention uses heads*head_dim projections',
    })
    try: worker(argv)
    finally:
        LlamaConfig.validate_architecture=original
        LlamaConfig.__class_validators__=original_validators


if __name__=='__main__':run(sys.argv[1:])
