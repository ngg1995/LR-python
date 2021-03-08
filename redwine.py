import pandas as pd
import numpy as np
import random
from matplotlib import pyplot as plt
from sklearn.linear_model import LogisticRegression
import itertools as it
from tqdm import tqdm
import pba

from LRF import *

### Import the data
wine_data = pd.read_csv('winequality-red.csv',index_col = None,usecols = ['volatile acidity','citric acid','chlorides','pH','sulphates','alcohol','quality'])

# Split the data into test/train factors and result and generate uncertain points
random.seed(587) # for reproducability best 587 760
goodwine = 7 # with with quality >= goodwine is considered high quality
results = wine_data['quality'] >= goodwine

train_data_index = random.sample([i for i in wine_data.index if results.loc[i]], k = 75) +  random.sample([i for i in wine_data.index if not results.loc[i]], k = 125)
train_data = wine_data.loc[train_data_index,[c for c in wine_data.columns if c != 'quality']]
train_results = results.loc[train_data_index]

uq_data_index = random.sample([i for i in train_data.index if wine_data.loc[i,'quality'] == goodwine], k = 5) + random.sample([i for i in train_data.index if wine_data.loc[i,'quality'] == goodwine-1], k = 5)
nuq_data_index = [i for i in train_data_index if i not in uq_data_index]

uq_data = train_data.loc[uq_data_index]
uq_results = pd.Series([pba.I(0,1)]*len(uq_data_index),index = uq_data_index,dtype = 'O')

nuq_data = train_data.loc[nuq_data_index]
nuq_results = train_results.loc[nuq_data_index]


### Fit logistic regression model on full dataset
base = LogisticRegression(max_iter=1000)
base.fit(train_data.to_numpy(),train_results.to_numpy())
# print(*zip(train_data.columns,*base.coef_))
### Fit UQ models
uq_models = uc_logistic_regression(train_data,train_results,uq_data)

### Fit models with missing data
nuq = LogisticRegression(max_iter=1000)
nuq.fit(nuq_data.to_numpy(),nuq_results.to_numpy())

# ### Get confusion matrix
# # Classify train data
# base_predict = base.predict(train_data)

# # CLASSIFY NO_UQ MODEL DATA 
# nuq_predict = nuq.predict(train_data)

# # CLASSIFY UQ MODEL 
# train_predict = pd.DataFrame(columns = uq_models.keys())

# for key, model in uq_models.items():
#     train_predict[key] = model.predict(train_data)
    
# predictions = []
# for i in train_predict.index:
#     predictions.append([min(train_predict.loc[i]),max(train_predict.loc[i])])

# with open('runinfo/redwine_cm.out','w') as f:
#     print('TRUE MODEL',file = f)
#     a,b,c,d = generate_confusion_matrix(train_results,base_predict)
#     print('TP=%i\tFP=%i\nFN=%i\tTN=%i' %(a,b,c,d),file = f)

#     # Calculate sensitivity and specificity
#     print('Sensitivity = %.3f' %(a/(a+c)),file = f)
#     print('Specificity = %.3f' %(d/(b+d)),file = f)

#     print('DISCARDED DATA MODEL',file = f)
#     aa,bb,cc,dd = generate_confusion_matrix(train_results,nuq_predict)
#     try:
#         ss = 1/(1+cc/aa)
#     except:
#         ss = None
#     try:    
#         tt = 1/(1+bb/dd)
#     except:
#         tt = None
#     print('TP=%s\tFP=%s\nFN=%s\tTN=%s' %(aa,bb,cc,dd),file = f)

#     # Calculate sensitivity and specificity
#     print('Sensitivity = %.3f' %(ss),file = f)
#     print('Specificity = %.3f' %(tt),file = f)

#     print('UQ MODEL',file = f)
    
#     aaai,bbbi,ccci,dddi = generate_confusion_matrix(train_results,predictions,throw = False)
#     try:
#         sssi = 1/(1+ccci/aaai)
#     except:
#         sssi = None
#     try:    
#         ttti = 1/(1+bbbi/dddi)
#     except:
#         ttti = None
        
#     print('TP=[%i,%i]\tFP=[%i,%i]\nFN=[%i,%i]\tTN=[%i,%i]' %(*aaai,*bbbi,*ccci,*dddi),file = f)

#     # Calculate sensitivity and specificity
#     print('Sensitivity = [%.3f,%.3f]\nSpecificity = [%.3f,%.3f]' %(*sssi,*ttti),file = f)
#     aaa,bbb,ccc,ddd,eee,fff = generate_confusion_matrix(train_results,predictions,throw = True)
#     try:
#         sss = 1/(1+ccc/aaa)
#     except:
#         sss = None
#     try:    
#         ttt = 1/(1+bbb/ddd)
#     except:
#         ttt = None
        
#     print('TP=%i\tFP=%i\nFN=%i\tTN=%i\nNP(+)=%i\tNP(-)=%i' %(aaa,bbb,ccc,ddd,eee,fff),file = f)

#     # Calculate sensitivity and specificity
#     print('Sensitivity = %.3f' %(sss),file = f)
#     print('Specificity = %.3f' %(ttt),file = f)

# ### Descriminatory Performance Plots
# # s,fpr,predictions = ROC(model = base, data = train_data, results = train_results)
# nuq_s,nuq_fpr,nuq_predictions = ROC(model = nuq, data = train_data, results = train_results)
# s_t, fpr_t, Sigma, Tau, Nu = UQ_ROC_alt(uq_models, train_data, train_results)

# s_i, fpr_i,uq_predictions = UQ_ROC(uq_models, train_data, train_results)

# densfig,axdens = plt.subplots(nrows = 2, sharex= True)

# for i,(p,u,nuqp,r) in enumerate(zip(predictions,uq_predictions,nuq_predictions,train_results.to_list())):
#     yd = np.random.uniform(-0.01,-.31)
#     if r:
#         # axdens[0].scatter(p,np.random.uniform(-0.1,0.1),color = 'k',marker = 'o',alpha = 0.5)
#         axdens[0].scatter(nuqp,np.random.uniform(0.01,0.31),color = '#DC143C',marker = 'o',alpha = 0.5)
#         axdens[0].plot([u[0],u[1]],[yd,yd],color = '#4169E1',alpha = 0.3)
#         axdens[0].scatter([u[0],u[1]],[yd,yd],color = '#4169E1',marker = '|')
#     else:
#         # axdens[1].scatter(p,np.random.uniform(-.1,0.1),color = 'k',marker = 'o',alpha = 0.5)
#         axdens[1].scatter(nuqp,np.random.uniform(0.11,.31),color = '#DC143C',marker = 'o',alpha = 0.5)
#         axdens[1].plot([u[0],u[1]],[yd,yd],color = '#4169E1',alpha = 0.3)
#         axdens[1].scatter([u[0],u[1]],[yd,yd],color = '#4169E1',marker = '|')
        
        
# axdens[0].set(ylabel = 'Outcome = 1',yticks = [],xlim=[0,1],xticks = [0,0.25,0.50,0.75,1])
# axdens[1].set(xlabel = '$\pi$',ylabel = 'Outcome = 0',yticks = [])
# densfig.tight_layout()

# rocfig,axroc = plt.subplots(1,1)
# axroc.plot([0,1],[0,1],'k:',label = 'Random Classifier')
# axroc.set(xlabel = '$fpr$',ylabel='$s$')
# # axroc.plot(fpr,s,'k',label = 'Base')
# axroc.plot(nuq_fpr,nuq_s,color='#DC143C',label='No Uncertainty')
# axroc.plot(fpr_t,s_t,'#4169E1',label='Uncertain (No prediction)')
# axroc.legend()
# rocfig.savefig('figs/redwine_ROC.png',dpi = 600)
# rocfig.savefig('../paper/figs/redwine_ROC.png',dpi = 600)
# densfig.savefig('figs/redwine_dens.png',dpi =600)
# densfig.savefig('../paper/figs/redwine_dens.png',dpi =600)


# with open('runinfo/redwine_auc.out','w') as f:
#     # print('NO UNCERTAINTY: %.3f' %auc(s,fpr), file = f)
#     print('MIDPOINTS: %.4F' %auc(nuq_s,nuq_fpr),file = f)
#     print('THROW: %.3f' %auc(s_t,fpr_t), file = f)
#     # print('INTERVALS: [%.3f,%.3f]' %(auc_int_min,auc_int_max), file = f)
    


# fig = plt.figure()
# ax = plt.axes(projection='3d',elev = 45,azim = -45,proj_type = 'ortho')
# ax.set_xlabel('$fpr$')
# ax.set_ylabel('$s$')
# # ax.set_zlabel('$1-\sigma,1-\\tau$')
# ax.plot(fpr_t,s_t,'#4169E1',alpha = 0.5)
# ax.plot3D(fpr_t,s_t,Sigma,'#FF8C00',label = '$\\sigma$')
# ax.plot3D(fpr_t,s_t,Tau,'#008000',label = '$\\tau$')
# # ax.plot3D(fpr,s,Nu,'k',label = '$1-\\nu$')

# ax.legend()

# plt.savefig('figs/redwine_ROC3D.png',dpi = 600)
# plt.savefig('../paper/figs/redwine_ROC3D.png',dpi = 600)
# plt.clf()

# plt.xlabel('$fpr$/$s$')
# plt.ylabel('$\\sigma$/$\\tau$')
# plt.plot(s_t,Sigma,'#FF8C00',label = '$\\sigma$ v $s$')
# plt.plot(fpr_t,Tau,'#008000',label = '$\\tau$ v $fpr$')
# plt.legend()


# plt.savefig('figs/redwine_ST.png',dpi = 600)
# plt.savefig('../paper/figs/redwine_ST.png',dpi = 600)

# plt.clf()

### Hosmer-Lemeshow
# hl_b, pval_b = hosmer_lemeshow_test(base,train_data,train_results,g = 10)

hl_nuq, pval_nuq = hosmer_lemeshow_test(nuq,train_data,train_results,g = 10)
hl_nuq0, pval_nuq0 = hosmer_lemeshow_test(nuq,nuq_data,nuq_results,g = 10)


hl_uq, pval_uq = UQ_hosmer_lemeshow_test(uq_models,train_data,train_results,g = 10)
hl_uq0, pval_uq0 = UQ_hosmer_lemeshow_test(uq_models,pd.concat([nuq_data,uq_data]),pd.concat([nuq_results,uq_results]),g = 10)


with open('runinfo/redwine_HL.out','w') as f:
    print('no UQ\nhl = %.3f, p = %.3f' %(hl_nuq0,pval_nuq0),file = f)
    print('no UQ(full)\nhl = %.3f, p = %.3f' %(hl_nuq,pval_nuq),file = f) 
    print('UQ\nhl = [%.3f,%.3f], p = [%.3f,%.3f]' %(*hl_uq0,*pval_uq0),file = f)
    print('UQ(full)\nhl = [%.3f,%.3f], p = [%.3f,%.3f]' %(*hl_uq,*pval_uq),file = f)
    
    