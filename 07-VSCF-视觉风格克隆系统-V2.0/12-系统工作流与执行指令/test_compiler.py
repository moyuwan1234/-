import copy, unittest
from compile_prompts import ROOT,read,compile,validate
EX=ROOT/'08-风格克隆案例库'/'STYLE-0001-极简黑白线描'
class TestCompiler(unittest.TestCase):
    def setUp(self): self.d=read(EX/'04-核心风格DNA.json'); self.t=read(EX/'05-主题输入示例.json')
    def test_general(self):
        z,e,s,n,m=compile(self.d); self.assertEqual(len(m['included_rule_ids']),13); self.assertIn('{{主题}}',s); self.assertIn('建筑',n); self.assertIn('植物',n)
    def test_bound(self):
        z,e,s,n,m=compile(self.d,self.t); self.assertEqual(m['included_rule_ids'],[r['规则编号'] for r in z['规则']]); self.assertIn('SUB-002',m['included_rule_ids']); self.assertNotIn('SUB-003',m['included_rule_ids']); self.assertNotIn('SUB-004',m['included_rule_ids'])
    def test_migration(self):
        _,_,_,_,a=compile(self.d,self.t); self.t['subject_category']='plant'; self.t['complexity']='high'; _,_,_,_,b=compile(self.d,self.t); cores={r['rule_id'] for r in self.d['rules'] if r['gene_type']=='core'}; self.assertTrue(cores<=set(a['included_rule_ids']) and cores<=set(b['included_rule_ids'])); self.assertIn('SUB-003',b['included_rule_ids']); self.assertIn('DEN-002',b['included_rule_ids']); self.assertNotIn('SUB-002',b['included_rule_ids'])
    def test_unknown_fallback(self):
        self.t['subject_category']='other'; self.t['complexity']='unknown'; *_,m=compile(self.d,self.t); self.assertIn('SUB-001',m['included_rule_ids'])
    def test_conflict(self):
        self.t['conflicts']=[{'resolved':False,'rule_id':'COL-001'}]; self.assertRaises(ValueError,compile,self.d,self.t)
    def test_duplicate(self):
        self.d['rules'].append(copy.deepcopy(self.d['rules'][0])); self.assertRaises(ValueError,validate,self.d)
    def test_core_condition(self):
        self.d['rules'][0]['condition']['subject_categories']=['plant']; self.assertRaises(ValueError,validate,self.d)
    def test_no_fallback(self):
        self.d['rules']=[r for r in self.d['rules'] if r['rule_id']!='SUB-001']; self.assertRaises(ValueError,validate,self.d)
    def test_fake_validation(self):
        self.d['status']='validated'; self.assertRaises(ValueError,validate,self.d)
    def test_draft(self): self.assertRaises(ValueError,compile,read(ROOT/'06-JSON结构化协议'/'通用JSON模板.json'))
if __name__=='__main__': unittest.main(verbosity=2)
