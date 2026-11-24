"""VSCF 2.0: deterministic, offline four-format prompt compiler."""
import argparse, json, re
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'06-JSON结构化协议'/'JSON-Schema.json'
CLASSES={'architecture','plant','person','animal','product','landscape','abstract','mixed','other'}
COMPLEX={'low','medium','high','unknown'}
TYPES=['core','stable','adaptive','negative']
ZH={'core':'核心','stable':'稳定','adaptive':'自适应','negative':'排斥'}
CATEGORY_ZH=dict(zip(['architecture','plant','person','animal','product','landscape','abstract','mixed','other'],['建筑','植物','人物','动物','产品','景观','抽象','混合','其他']))
COMPLEX_ZH={'low':'低','medium':'中','high':'高','unknown':'未知'}

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def validate(d):
    schema=read(SCHEMA); Draft202012Validator.check_schema(schema); Draft202012Validator(schema).validate(d)
    rules=d['rules']; ids=[r['rule_id'] for r in rules]; src=[s['source_id'] for s in d['sources']]
    if len(ids)!=len(set(ids)): raise ValueError('重复规则ID / duplicate rule ID')
    if len(src)!=len(set(src)): raise ValueError('重复来源ID / duplicate source ID')
    for r in rules:
        if any(e['source_id'] not in src for e in r['evidence']): raise ValueError('证据来源不存在: '+r['rule_id'])
        if r['gene_type']=='core' and any(r['condition'].values()): raise ValueError('核心规则不得有条件: '+r['rule_id'])
        if d['dimensions'][r['dimension']]['status']!='analyzed': raise ValueError('未分析维度含规则: '+r['rule_id'])
        for field in ['observation','instruction','allowed_variation','validation']:
            if not all(s.strip() for s in r[field].values()): raise ValueError('双语字段不得为空: '+r['rule_id'])
        if d['status']=='validated' and any(e['type']=='hypothetical' for e in r['evidence']): raise ValueError('假设证据不可标记已验证')
    for k,s in d['dimensions'].items():
        if s['status']=='analyzed' and not any(r['dimension']==k and r['gene_type']!='free' for r in rules): raise ValueError('analyzed维度缺少非自由规则: '+k)
    if d['status'] in ('draft','deprecated'): raise ValueError('草稿或已废弃资产不可编译')
    if not any(r['gene_type']=='core' for r in rules): raise ValueError('缺少核心规则')
    if not any(r['gene_type']=='adaptive' and not any(r['condition'].values()) for r in rules): raise ValueError('缺少通用自适应回退')
    return d

def check_theme(t):
    for k in ('theme','subject','scene','required_features'):
        if not isinstance(t.get(k),dict) or not all(isinstance(t[k].get(l),str) and t[k][l].strip() for l in ('zh','en')): raise ValueError('主题双语字段不完整: '+k)
    if t.get('subject_category') not in CLASSES or t.get('complexity') not in COMPLEX: raise ValueError('非法主题分类或复杂度')
    if not isinstance(t.get('aspect_ratio'),str) or not (t['aspect_ratio']=='unspecified' or re.fullmatch(r'[1-9]\d*:[1-9]\d*',t['aspect_ratio'])): raise ValueError('非法画幅')
    if not isinstance(t.get('conflicts'),list): raise ValueError('缺少冲突记录')
    if any(not isinstance(c,dict) or c.get('resolved') is not True or not isinstance(c.get('resolution'),str) or not c['resolution'].strip() for c in t['conflicts']): raise ValueError('存在未解决主题冲突；停止编译')
    return t

def matches(r,t):
    c=r['condition']; return (not c['subject_categories'] or t['subject_category'] in c['subject_categories']) and (not c['complexities'] or t['complexity'] in c['complexities'])

def condition_text(r,lang):
    c=r['condition']; chunks=[]
    if c['subject_categories']: chunks.append(('主体类别：' if lang=='zh' else 'subject category: ')+('、' if lang=='zh' else ', ').join(CATEGORY_ZH[x] if lang=='zh' else x for x in c['subject_categories']))
    if c['complexities']: chunks.append(('复杂度：' if lang=='zh' else 'complexity: ')+('、' if lang=='zh' else ', ').join(COMPLEX_ZH[x] if lang=='zh' else x for x in c['complexities']))
    return ('；' if lang=='zh' else '; ').join(chunks) if chunks else ('任意' if lang=='zh' else 'any')

def compile(d,t=None):
    validate(d)
    if t is not None: check_theme(t)
    rules=sorted((r for r in d['rules'] if r['gene_type'] in TYPES and (t is None or matches(r,t))),key=lambda r:(TYPES.index(r['gene_type']),-r['priority'],r['rule_id']))
    tv=t if t is not None else read(ROOT/'06-JSON结构化协议'/'主题输入模板.json')
    def rule_out(r,lang):
        if lang=='zh': return {'规则编号':r['rule_id'],'维度':r['dimension'],'基因类型':ZH[r['gene_type']],'执行规则':r['instruction']['zh'],'允许变化':r['allowed_variation']['zh'],'适用条件':condition_text(r,'zh'),'优先级':r['priority']}
        return {'rule_id':r['rule_id'],'dimension':r['dimension'],'gene_type':r['gene_type'],'instruction':r['instruction']['en'],'allowed_variation':r['allowed_variation']['en'],'condition':condition_text(r,'en'),'priority':r['priority']}
    zh={'任务类型':'通用视觉风格克隆','风格编号':d['style_id'],'版本':d['version'],'风格名称':d['name']['zh'],'模式':'通用模板' if t is None else '主题绑定','主题变量':{'主题':tv['theme']['zh'],'主体':tv['subject']['zh'],'场景':tv['scene']['zh'],'主体类别':CATEGORY_ZH[tv['subject_category']] if t is not None else '{{主体类别}}','复杂度':COMPLEX_ZH[tv['complexity']] if t is not None else '{{复杂度}}','画幅':tv['aspect_ratio'] if t is not None else '{{画幅}}','必要特征':tv['required_features']['zh']},'约束':'核心规则不可改变；排斥规则必须遵守；条件规则仅在条件满足时执行；冲突须解决后再生成。','规则':[rule_out(r,'zh') for r in rules]}
    en={'task_type':'universal_visual_style_cloning','style_id':d['style_id'],'version':d['version'],'style_name':d['name']['en'],'mode':'general_template' if t is None else 'theme_bound','theme_variables':{'theme':tv['theme']['en'],'subject':tv['subject']['en'],'scene':tv['scene']['en'],'subject_category':tv['subject_category'] if t is not None else '{{subject_category}}','complexity':tv['complexity'] if t is not None else '{{complexity}}','aspect_ratio':tv['aspect_ratio'] if t is not None else '{{aspect_ratio}}','required_features':tv['required_features']['en']},'constraints':'Preserve core rules; obey negative rules; apply conditional rules only when conditions match; resolve conflicts before generation.','rules':[rule_out(r,'en') for r in rules]}
    v=zh['主题变量']; intro='主题：'+v['主题']+'；主体：'+v['主体']+'；场景：'+v['场景']+'；类别：'+v['主体类别']+'；复杂度：'+v['复杂度']+'；画幅：'+v['画幅']+'；必要特征：'+v['必要特征']+'。'
    def text_rule(r): return f"{r['instruction']['zh']}（允许变化：{r['allowed_variation']['zh']}；条件：{condition_text(r,'zh')}）"
    short=intro+zh['约束']+'\n'+'\n'.join(ZH[g]+'：'+'；'.join(text_rule(r) for r in rules if r['gene_type']==g)+'。' for g in TYPES if any(r['gene_type']==g for r in rules))+'\n'
    natural='请按照以下主题变量进行创作。'+intro+'\n\n'+zh['约束']+'\n\n'+'\n\n'.join({'core':'整体必须严格保持以下核心风格：','stable':'在允许范围内保持以下稳定视觉关系：','adaptive':'根据对象与复杂度应用以下适配规则：','negative':'避免以下会破坏风格的表现：'}[g]+'。'.join(text_rule(r) for r in rules if r['gene_type']==g)+'。' for g in TYPES if any(r['gene_type']==g for r in rules))+'\n'
    ids=[r['rule_id'] for r in rules]
    assert ids==[r['规则编号'] for r in zh['规则']]==[r['rule_id'] for r in en['rules']]
    for r in rules:
        assert text_rule(r) in short and text_rule(r) in natural
    manifest={'style_id':d['style_id'],'style_version':d['version'],'asset_status':d['status'],'mode':en['mode'],'included_rule_ids':ids,'excluded_rule_ids':[r['rule_id'] for r in d['rules'] if r['rule_id'] not in ids],'structural_checks':'pass','semantic_translation_review':'pending','visual_generation_validation':'not_run'}
    return zh,en,short,natural,manifest

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('dna'); p.add_argument('--theme'); p.add_argument('--out',required=True); a=p.parse_args()
    zh,en,short,natural,m=compile(read(a.dna),read(a.theme) if a.theme else None); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    dump(out/'01-中文JSON.json',zh); dump(out/'02-英文JSON.json',en); (out/'03-中文简易提示词.md').write_text(short,encoding='utf-8'); (out/'04-自然语言提示词.md').write_text(natural,encoding='utf-8'); dump(out/'编译检查记录.json',m)
    print('PASS:',len(m['included_rule_ids']),'rules; four formats; visual validation not run')
if __name__=='__main__': main()
