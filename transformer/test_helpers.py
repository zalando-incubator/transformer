from transformer.helpers import zip_kv_pairs
from transformer.request import Header


class TestZipKVPairs:
    def test_it_returns_a_dict_given_a_list_of_named_tuples(self):
        name = "some name"
        value = "some value"

        result = zip_kv_pairs([Header(name=name, value=value)])

        assert isinstance(result, dict)
        assert result[name] == value
