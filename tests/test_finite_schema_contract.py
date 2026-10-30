import unittest
from checks.finite_schema import schema_check,check_schema
from checks.validation_common import ValidationError

class FiniteSchemaContract(unittest.TestCase):
    def test_explicit_nullable_type_union_is_finite_and_strict(self):
        from checks.finite_schema import schema_check
        for value in (None,'2026-10-24'):
            schema_check(value,{'type':['null','string'],'pattern':'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'})
        for value in (True,1,{},'tomorrow'):
            with self.subTest(value=value),self.assertRaises(AssertionError):
                schema_check(value,{'type':['null','string'],'pattern':'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'})
        for types in ([],['string','string'],['string',True]):
            with self.assertRaises(AssertionError):schema_check(None,{'type':types})

    def test_unknown_unused_branch_and_unsupported_type_union_rejected(self):
        for schema in ({'properties':{'not_present':{'$ref':'ignored.json'}}},{'items':{'allOf':[]}},{'type':['string','unknown']},{'additionalProperties':{'type':'string'}}):
            with self.subTest(schema=schema),self.assertRaises(ValidationError):schema_check({},schema)
    def test_schema_shapes_strict_even_when_value_has_other_type(self):
        for schema in ({'minItems':True},{'minLength':-1},{'required':'id'},{'required':['id','id']},{'properties':[]},{'items':[]},{'enum':[]},{'pattern':12}):
            with self.subTest(schema=schema),self.assertRaises(ValidationError):schema_check(None,schema)
        with self.assertRaisesRegex(AssertionError,'invalid finite pattern'):check_schema({'pattern':'['})
    def test_finite_primitives_and_boolean_integer_enum_boundaries(self):
        for value,schema in ((False,{'type':'boolean'}),(1,{'type':'integer'}),(1.5,{'type':'number'}),(None,{'enum':[None,'unset']}),('机制',{'type':'string','minLength':2,'pattern':'^机制$'})):
            with self.subTest(value=value):schema_check(value,schema)
        for value,schema in ((True,{'type':'integer'}),(False,{'enum':[0]}),(1,{'type':'boolean'}),(float('nan'),{'type':'number'}),(float('inf'),{})):
            with self.subTest(value=value),self.assertRaises(ValidationError):schema_check(value,schema)
    def test_unknown_properties_boolean_policy_and_nested_json(self):
        schema_check({'extra':[1,{'nested':'valid'}]},{'type':'object','additionalProperties':True})
        for value,schema in (({'extra':1},{'type':'object','additionalProperties':False}),({1:'not a JSON key'},{}),({'extra':object()},{'additionalProperties':True}),([float('nan')],{})):
            with self.subTest(value=value),self.assertRaises(ValidationError):schema_check(value,schema)
    def test_neighbor_optional_unused_branch_is_legal_if_supported(self):
        schema={'type':'object','required':['id'],'properties':{'id':{'type':'string'},'optional':{'type':'array','minItems':1,'items':{'enum':[None,'known']}}},'additionalProperties':False}
        schema_check({'id':'one'},schema);schema_check({'id':'one','optional':[None,'known']},schema)
        with self.assertRaises(ValidationError):schema_check({'id':'one','optional':[]},schema)
    def test_array_upper_bound_is_inclusive_and_nested(self):
        schema={'type':'object','properties':{'rows':{'type':'array','minItems':1,'maxItems':2,'items':{'type':'integer'}}}}
        for rows in ([1],[1,2]):schema_check({'rows':rows},schema)
        with self.assertRaisesRegex(ValidationError,'schema maxItems'):schema_check({'rows':[1,2,3]},schema)
        with self.assertRaisesRegex(ValidationError,'schema minItems'):schema_check({'rows':[]},schema)
    def test_zero_array_limit_and_nonarray_neighbor(self):
        schema_check([],{'maxItems':0})
        schema_check(None,{'maxItems':0})
        with self.assertRaisesRegex(ValidationError,'schema maxItems'):schema_check([None],{'maxItems':0})
    def test_invalid_array_upper_bounds_rejected_in_absent_branch(self):
        for bound in (-1,True,False,1.5,'2',None):
            with self.subTest(bound=bound),self.assertRaisesRegex(ValidationError,'nonnegative integer bound'):
                schema_check({}, {'properties':{'absent':{'maxItems':bound}}})
    def test_enum_nested_boolean_does_not_equal_numeric_and_objects_ignore_key_order(self):
        schema_check({'b':[None,True],'a':1},{'enum':[{'a':1,'b':[None,True]}]})
        for value,schema in (({'x':False},{'enum':[{'x':0}]}),([{'x':True}],{'enum':[[{'x':1}]]}),(None,{'enum':[None,None]}),(None,{'enum':[float('nan')]})):
            with self.subTest(value=value),self.assertRaises(ValidationError):schema_check(value,schema)

if __name__=='__main__':unittest.main()
