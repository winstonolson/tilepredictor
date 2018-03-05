import numpy as np

def load_model(modelf,**kwargs):
    from keras.models import _clone_sequential_model, Sequential, \
        load_model as _load_model
    flatten = kwargs.pop('flatten',False)
    model = _load_model(modelf,**kwargs)
    if flatten and model.layers[0].name.startswith('sequential_'):
        _model = _clone_sequential_model(model.layers[0])
        for layer in model.layers[1:]:
            _model.add(layer)
        model = _model
    return model

def backend():
    from keras import backend as _backend
    return _backend

def update_base_outputs(model_base,output_shape,optparam,hidden_type='fc'):
    from keras.models import Model, Sequential
    from keras.layers import Dense, Input
    from keras.regularizers import l2 as activity_l2
    from keras.constraints import max_norm as max_norm_constraint
    
    n_hidden,n_classes = output_shape
    print('output_shape: "%s"'%str((output_shape)))
    print('Adding %d x %d relu hidden + softmax output layer'%(n_hidden,
                                                               n_classes))

    obj_lambda2 = optparam.get('obj_lambda2',0.0025)
    obj_param = dict(activity_regularizer=activity_l2(obj_lambda2))

    max_norm=optparam.get('max_norm',np.inf)
    if max_norm!=np.inf:
        obj_param['kernel_constraint']=max_norm_constraint(max_norm)

    model_input = model_base.layers[0].input
    model_input_shape = model_base.layers[0].input_shape
    print('model_input_shape=%s'%str(model_input_shape))
    
    if hidden_type=='fc':
        hidden_layer = Dense(n_hidden, activation='relu')
    else:
        print('Unknown hidden_type "%s", using "fc"'%hidden_type)
        hidden_layer = Dense(n_hidden, activation='relu')

    output_layer = Dense(n_classes, activation='softmax', **obj_param)

    mclass = model_base.__class__.__name__
    if mclass == 'Sequential':
        print("Using Sequential model")
        model = model_base
        model.add(hidden_layer)
        model.add(output_layer) 
    else:
        print("Using functional API")
        #model = Model(inputs=model_base.inputs, outputs=model_base.outputs)
        #model = hidden_layer(model)
        #model = output_layer(model)

        model = Sequential()
        model.add(model_base)        
        model.add(hidden_layer)
        model.add(output_layer)        

    model.n_base_layers = len(model_base.layers)
    model.n_top_layers = len(model.layers)-model.n_base_layers
    
    return model

def model_transform(X,model,layer=0):
    from keras.backend import backend as _backend
    layer = model.layers[l]
    func = _backend.function([layer.get_input_at(0),_backend.learning_phase()],
                             [layer.get_output_at(0)])
    return func([X])[0]

def model_init(model_base, model_flavor, state_dir, optparam, **params):
    #from keras.optimizers import Adam as Optimizer
    #optparams   = dict(lr=optparam['lr_min'],
    #                   beta_1=optparam['beta_1'],
    #                   beta_2=optparam['beta_2'],
    #                   decay=optparam['weight_decay'],
    #                   epsilon=optparam['tol'])    
    from keras.optimizers import Nadam as Optimizer
    from keras import backend as _backend
    from keras.models import load_model

    verbose     = params.get('verbose',False)
    overwrite   = params.pop('overwrite',True)

    print('Initialzing optimizer')
    lr_mult = params.pop('lr_mult',1.0)
    optparams   = dict(lr=optparam['lr_min'],
                       beta_1=optparam['beta_1'],
                       beta_2=optparam['beta_2'],
                       schedule_decay=optparam['weight_decay'],
                       epsilon=optparam['tol'])
    params.setdefault('loss','categorical_crossentropy')
    params['optimizer'] = Optimizer(**optparams)
    
    print('Initialzing model functions')
    model_backend = _backend.backend()
    model_xform = lambda X,l=0: model_transform(X,model_base,l)
    model_pred  = lambda X,batch_size=32: model_base.predict(X,verbose=verbose,
                                                             batch_size=batch_size)
    model_batch = lambda X,y: model_base.train_on_batch(X,y)
    #model_save  = lambda weightf: model_base.save_weights(weightf,
    #                                                      overwrite=overwrite)

    model_load  = lambda modelf: load_model(modelf)
    return dict(package='keras',backend=model_backend,flavor=model_flavor,
                base=model_base,batch=model_batch,predict=model_pred,
                transform=model_xform,load_base=model_load,
                state_dir=state_dir,params=params)
