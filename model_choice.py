#! usr/bin/python3

# -*- coding: utf8 -*-

import keras
import csv
from keras.callbacks import TensorBoard, EarlyStopping, ModelCheckpoint
from keras import layers, models, optimizers
from keras import backend as K
from keras.utils import to_categorical
from capsulelayers import CapsuleLayer, PrimaryCap, Length, Mask
from keras.models import Sequential
from keras.layers import Conv2D, GlobalAveragePooling1D, MaxPooling2D
from keras.layers import Dense, Dropout, Activation, Embedding, BatchNormalization, Flatten
from keras.optimizers import SGD
from keras.wrappers.scikit_learn import KerasClassifier
from imblearn.over_sampling import SMOTE, ADASYN, RandomOverSampler

import numpy as np

from sklearn.preprocessing import LabelBinarizer, MinMaxScaler, LabelEncoder, RobustScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
from sklearn.metrics import classification_report

# dos =1 / probe = 4 / r2l = 3 / u2r = 2 / normal =5
def transform(x):
    return {
        'back': 1,
        'udpstorm': 1,
        'buffer_overflow': 2,
        'ftp_write': 3,
        'guess_passwd': 3,
        'imap': 3,
        'ipsweep': 4,
        'land': 1,
        'loadmodule': 2,
        'multihop': 3,
        'neptune': 1,
        'nmap': 4,
        'perl': 2,
        'phf': 3,
        'pod': 1,
        'portsweep': 4,
        'rootkit': 2,
        'satan': 4,
        'smurf': 1,
        'spy': 3,
        'teardrop': 1,
        'warezclient': 3,
        'warezmaster': 3,
        'apache2': 1,
        'mailbomb': 1,
        'processtable': 1,
        'mscan': 4,
        'saint': 4,
        'sendmail': 3,
        'named': 3,
        'snmpgetattack': 3,
        'snmpguess': 3,
        'xlock': 3,
        'xsnoop': 3,
        'worm': 3,
        'httptunnel': 2,
        'ps': 2,
        'sqlattack': 2,
        'xterm': 2,
        'normal': 5
    }[x]


def generate_model(shape):
    # define the model
    model = keras.models.Sequential()

    model.add(Dense(82, input_dim=shape, activation='relu'))
    model.add(Dropout(0.1))
    model.add(Dense(164, activation='relu'))
    model.add(Dense(164, activation='relu'))
    model.add(Dense(82, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(41, activation='softmax'))
    model.add(Dropout(0.2))
    model.add(Dense(20, activation='softmax',name='output'))
    model.add(Dropout(0.2))
    model.add(Dense(5, activation='softmax'))

    return model

def deep_mlp_model(shape):
    '''
    https://github.com/jvmancuso/DeepIDS/blob/master/develop/2017-08-07-jm-KerasTestReLU.ipynb '''
    model = keras.models.Sequential()

    model.add(Dense(4096, input_dim=shape))
    model.add(Activation('relu'))
    model.add(BatchNormalization())
    model.add(Dense(2048))
    model.add(Activation('relu'))
    model.add(BatchNormalization())
    model.add(Dense(1024))
    model.add(Activation('relu'))
    model.add(BatchNormalization(name='output'))
    model.add(Dense(5, activation='softmax'))

    return model

def generate_cnn_model(shape):
    '''
        Model from a reasearch paper
        https://www.researchgate.net/publication/319717354_A_Few-shot_Deep_Learning_Approach_for_Improved_Intrusion_Detection
    '''
    model = Sequential()
    model.add(Conv2D(64, (3, 1), activation='relu', input_shape=(shape, 1, 1)))
    model.add(Conv2D(64, (3, 1), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 1)))
    model.add(Conv2D(128, (3, 1), activation='relu'))
    model.add(Conv2D(128, (3, 1), activation='relu', padding="same"))
    model.add(Conv2D(128, (3, 1), activation='relu', padding="same"))
    model.add(MaxPooling2D(pool_size=(2, 1)))
    model.add(Conv2D(256, (3, 1), activation='relu', padding="same"))
    model.add(Conv2D(256, (3, 1), activation='relu', padding="same"))
    model.add(Conv2D(256, (3, 1), activation='relu', padding="same"))
    model.add(MaxPooling2D(pool_size=(2, 1)))
    model.add(Flatten())
    model.add(Dense(100, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(20, kernel_initializer='normal', activation='relu',name='output'))
    model.add(Dense(5, kernel_initializer='normal', activation='softmax'))
    return model


def create_model(optimizer='rmsprop', init='glorot_uniform'):

    model = keras.models.Sequential()

    model.add(Dense(82, input_dim=41, activation='relu'))
    model.add(Dropout(0.1))
    model.add(Dense(164, kernel_initializer=init, activation='relu'))
    model.add(Dense(164, kernel_initializer=init, activation='relu'))
    model.add(Dense(82, kernel_initializer=init, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(41, kernel_initializer=init, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(20, kernel_initializer=init, activation='relu',name='output'))
    model.add(Dropout(0.2))
    model.add(Dense(5, kernel_initializer=init, activation='softmax'))

    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer, metrics=['accuracy'])
    return model


def preporcess(data, dataTest, CNN=False):
    scaler = MinMaxScaler()
    encoder = LabelBinarizer()
    encoder2 = LabelEncoder()

    x_train = data[:, np.arange(0, 41)]
    x_test = dataTest[:, np.arange(0, 41)]

    encoder2.fit(x_train[:,1])
    x_train[:, 1] = encoder2.transform(x_train[:, 1])
    x_test[:, 1] = encoder2.transform(x_test[:, 1])

    encoder2.fit(x_train[:,2])
    x_train[:, 2] = encoder2.transform(x_train[:, 2])
    x_test[:, 2] = encoder2.transform(x_test[:, 2])

    encoder2.fit(x_train[:,3])
    x_train[:, 3] = encoder2.transform(x_train[:, 3])
    x_test[:, 3] = encoder2.transform(x_test[:, 3])

    print(x_test)
    scaler.fit(x_train)
    x_train = scaler.transform(x_train)
    scaler.fit(x_test)
    x_test = scaler.transform(x_test)
    print(x_test)

    train_label = data[:, 41]
    y_train = [transform(attacktype) for attacktype in train_label]

    test_label = dataTest[:, 41]
    y_test = [transform(attacktype) for attacktype in test_label]

    print(np.shape(x_train))
    # Oversampled low classes => Meilleurs résultat pour les classes avec peu d'exemples
    print("Oversampling train dataset")
    #x_train , y_train = SMOTE(ratio='auto').fit_sample(x_train, y_train)

    ros = RandomOverSampler(ratio='minority', random_state=10)
    x_train, y_train = ros.fit_sample(x_train, y_train)

    print(np.shape(x_train))
    # Transform to binary
    y_train = encoder.fit_transform(y_train)
    y_test = encoder.fit_transform(y_test)

    if(CNN):
        x_final_train = []
        x_final_test = []
        for x in x_train:
            sample = x.reshape([41, 1, 1])
            x_final_train.append(sample)
        x_train = np.array(x_final_train)

        for x in x_test:
            sample = x.reshape([41, 1, 1])
            x_final_test.append(sample)
        x_test = np.array(x_final_test)

        print(np.shape(x_train))

    # Generation d'un dataset de validation
    seed = 9
    np.random.seed(seed)
    x_validation, x_test, y_validation, y_test = train_test_split(
        x_test, y_test, test_size=0.70, random_state=seed)

    return x_train, y_train, x_validation, y_validation, x_test, y_test


def eval(model, x_test, y_test):
    score = model.evaluate(x_test, y_test, verbose=1)
    print("loss on test data:", score[0])
    print("accuracy on test data:", score[1]*100, "%")


def main():

    input_list = ["1. MLP", "2. CNN2D", "3. DeepMLP", "4. Sklearn Classifier"]

    filereader = csv.reader(open("Data/KDDTrain+.txt"), delimiter=",")
    data = np.array(list(filereader))

    filereaderTest = csv.reader(open("Data/KDDTest+.txt"), delimiter=",")
    dataTest = np.array(list(filereaderTest))

    P1 = input("Choisissez le reseau: " + ' '.join(input_list) + "\n")
    CNN = False
    if(P1 == '2'):
        CNN = True

    x_train, y_train, x_validation, y_validation, x_test, y_test = preporcess(
        data, dataTest, CNN)

    if (P1 == '1'):
         ### MLP model ###
        model = generate_model(41)
        model.compile(loss='categorical_crossentropy',
                      optimizer=optimizers.Adam(lr=0.001), metrics=['accuracy'])

    elif (P1 == '2'):
        ### CNN 2D model ##
        model = generate_cnn_model(41)

        # initiate RMSprop optimizer
        opt = optimizers.RMSprop()
        model.compile(loss='categorical_crossentropy',
                      optimizer=opt, metrics=['accuracy'])
    elif (P1 == '3'):
        ### Deep MLP ###
        model = deep_mlp_model(41)

        opt = optimizers.Adam()
        model.compile(opt, 'categorical_crossentropy', metrics = ['acc'])

    elif (P1 == '4'):

        model = KerasClassifier(build_fn=create_model, verbose=0)

        # grid search epochs, batch size and optimizer
        opt = ['rmsprop', 'adam']
        init = ['glorot_uniform', 'normal', 'uniform']
        epochs = [5, 10, 20]
        batches = [50]

        param_grid = dict(optimizer=opt, epochs=epochs,
                          batch_size=batches, init=init)
        grid = GridSearchCV(estimator=model, param_grid=param_grid, verbose=10)
        grid_result = grid.fit(x_train, y_train)
        # summarize results
        print("Test on best: %f" % grid_result.score(x_test, y_test))
        print("Best: %f using %s" %
              (grid_result.best_score_, grid_result.best_params_))
        means = grid_result.cv_results_['mean_test_score']
        stds = grid_result.cv_results_['std_test_score']
        params = grid_result.cv_results_['params']

        for mean, stdev, param in zip(means, stds, params):
            print("%f (%f) with: %r" % (mean, stdev, param))

    if (P1 != '4')
        stopper = EarlyStopping(monitor='val_acc', patience = 3, mode='auto')

        model.fit(x_train, y_train, epochs=10, batch_size=50, validation_data=(x_validation, y_validation),callbacks = [stopper])

        intermediate_layer_model = models.Model(inputs=model.input,
                                 outputs=model.get_layer('output').output)
        pred_x_train = intermediate_layer_model.predict(x_train, batch_size=50)
        pred_x_test = intermediate_layer_model.predict(x_test, batch_size=50)

        # Scale [0-1] for SVM learning
        scaler = MinMaxScaler()
        scaler.fit(pred_x_train)
        pred_x_train = scaler.fit_transform(pred_x_train)
        pred_x_test = scaler.fit_transform(pred_x_test)

        #print("Train a Random Forest model")
        #rf = RandomForestClassifier(n_estimators=100, criterion="entropy", random_state=1,verbose=2)
        #rf.fit(pred_x_train,y_train)
        
        print("Train SVM Classifier with One Vs All strategy")
        #Preprocess for SVM
        lb = LabelBinarizer()
        lb.fit([1,2,3,4,5])
        y_train_1d = lb.inverse_transform(y_train)
        y_test_1d =  lb.inverse_transform(y_test)
        lin_clf = svm.LinearSVC(verbose=2,max_iter=10000)
        lin_clf.fit(pred_x_train,y_train_1d)

        #y_pred_test_rf = rf.predict(pred_x_test)
        y_pred_test_svm = lin_clf.predict(pred_x_test)
        y_pred_test_svm_bin = lb.fit_transform(y_pred_test_svm)
        #print("Mean accuracy: %f" % rf.score(pred_x_test,y_test))
        print("Mean accuracy: %f" % lin_clf.score(pred_x_test,y_test_1d))
        #print(classification_report(y_test, y_pred_test_rf))

        print(classification_report(y_test, y_pred_test_svm_bin))
        
    eval(model, x_test, y_test)


if __name__ == "__main__":
    main()
