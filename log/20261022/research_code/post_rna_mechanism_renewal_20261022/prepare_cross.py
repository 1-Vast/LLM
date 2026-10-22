"""Bind sealed first opinions to actual reciprocal-review requests."""
import hashlib,json
from api_round import P,ROLES,digest

def main():
    seal=json.loads((P/'INDEPENDENT_RESPONSE_SEAL.json').read_text())
    drafts='';inputs={}
    for role in ROLES:
        path=P/'api_reviews'/role/'RESPONSE.md';raw=path.read_bytes()
        assert digest(raw)==seal['roles'][role]['response_sha256']
        inputs[str(path.relative_to(P))]=digest(raw)
        drafts+='\n\n--- INDEPENDENT '+role+' ---\n'+raw.decode('utf-8')
    extra=''
    for name in ['ROOT_CROSS_QUESTIONS.md','CHEAP_AUDIT_PROTOCOL.md','CHEAP_AUDIT_RESULT.json']:
        raw=(P/name).read_bytes();inputs[name]=digest(raw);extra+='\n\n--- '+name+' ---\n'+raw.decode('utf-8')
    for role in ROLES:
        dest=P/'api_reviews'/(role+'_cross');dest.mkdir()
        prompt='你是先前的 '+role+' 角色。下面是你和另外两名角色的真实首评原文及root已执行的反例检查。请认真交叉质疑，并明确修正你自己的错误。\n'+drafts+extra
        with (dest/'PROMPT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(prompt)
    with (P/'CROSS_INPUT_SEAL.json').open('x',encoding='utf-8') as f:json.dump(dict(inputs=inputs,independent_responses_checked=True),f,indent=2)

if __name__=='__main__':main()
