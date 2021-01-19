from dal import autocomplete


class AutocompleteSingleWidget(autocomplete.ListSelect2):
    autocomplete_function = "single_autocomplete_init"


class AutocompleteMultiWidget(autocomplete.ModelSelect2Multiple):
    autocomplete_function = "multi_autocomplete_init"
