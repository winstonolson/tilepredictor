from warnings import warn
_model_id = 'InceptionV3'
MAX_BLOCK = 12 # inception max block=11
def model_init(input_shape,**kwargs):
    from keras.applications import InceptionV3    

    assert(len(input_shape)==3 and input_shape[2]==3)

    fix_base = kwargs.pop('fix_base',True)
    if not fix_base:
        warn('%s model fix_base=False, training may take a long time'%_model_id)

    base_model = InceptionV3(weights="imagenet", include_top=False,
                             pooling='avg', input_shape=input_shape)

    n_layers = len(base_model.layers)
    max_block = kwargs.pop('max_block',MAX_BLOCK)         
    max_layer = kwargs.pop('max_layer',n_layers)
    max_layer = min(n_layers,max_layer) if max_layer>0 else n_layers+max_layer
    
    
    if fix_base:
        print('Fixing %s base_model layers'%_model_id)
        # first: train only the top layers (which were randomly initialized)
        trainable = False # fix blocks until we hit max_block
        for i,layer in enumerate(base_model.layers):
            lname = layer.name
            if not trainable and max_block < MAX_BLOCK:
                if lname.startswith('mixed'):                    
                    spl = lname.split('_')
                    lid = int(spl[0].replace('mixed',''))
                    if lid>max_block:
                        trainable = True
                        base_model.layers[i-1].trainable = trainable
                
            layer.trainable = trainable

    return dict(model=base_model,lr_mult=0.1)

