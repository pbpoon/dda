from django.core.exceptions import ObjectDoesNotExist
 
 
def model_to_dict(obj, exclude=['AutoField', 'ForeignKey', \
    'OneToOneField']):
    '''
        serialize model object to dict with related objects

        author: Vadym Zakovinko <vp@zakovinko.com>
        date: January 31, 2011
        http://djangosnippets.org/snippets/2342/
    '''
    tree = {}
    for field_name in obj._meta.get_all_field_names():
        try:
            field = getattr(obj, field_name)
        except (ObjectDoesNotExist, AttributeError):
            continue
 
        if field.__class__.__name__ in ['RelatedManager', 'ManyRelatedManager']:
            if field.model.__name__ in exclude:
                continue
 
            if field.__class__.__name__ == 'ManyRelatedManager':
                exclude.append(obj.__class__.__name__)
            subtree = []
            for related_obj in getattr(obj, field_name).all():
                value = model_to_dict(related_obj, \
                    exclude=exclude)
                if value:
                    subtree.append(value)
            if subtree:
                tree[field_name] = subtree
 
            continue
 
        field = obj._meta.get_field_by_name(field_name)[0]
        if field.__class__.__name__ in exclude:
            continue
 
        if field.__class__.__name__ == 'RelatedObject':
            exclude.append(field.model.__name__)
            tree[field_name] = model_to_dict(getattr(obj, field_name), \
                exclude=exclude)
            continue
 
        value = getattr(obj, field_name)
        if value:
            tree[field_name] = value
 
    return tree