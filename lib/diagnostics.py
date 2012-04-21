# -*- coding: utf-8 -*-
"""
"""
import numpy as np
from scipy.stats import f
from scipy.optimize import brentq


def calc_max_chi(N,P,best_chi):
    fval=f.isf(0.05,P,N-P)
    return best_chi*(fval*P/float(N-P)+1)

def f_compare(N,P,new_chi,best_chi,nfix=1.):
    """
    Returns the probalitiy for two given parameter sets.
    nfix is the number of fixed parameters.
    
    
    """  
    #print new_chi, best_chi, N, P
    P=P+nfix
    return f.cdf((new_chi/best_chi-1)*(N-P)/nfix,nfix,N-P)

def copy_vals(params):
    "Saves the values of paras and errs in temporay dict"
    tmp_params={}
    for para_key in params:
        tmp_params[para_key]=(params[para_key].value,params[para_key].stderr)
    return tmp_params
    
def restore_vals(tmp_params,params):
    "Restores the values of params from a temporay dict"
    for para_key in params:
        params[para_key].value, params[para_key].stderr=tmp_params[para_key]
        
def p_trace_to_dict(p_tr,params):
    """
    p_tr has following form:
        ([[p1, p2,...],[p1, p2,...]],[res_prob1,res_prob2..])
    Returns a dict with p-names and prob as keys and lists as their values. 
    """
    out={}   
    print params.keys()
    for name in params.keys():       
        out[name]=np.array([l.pop(0) for l in p_tr[0]])
    out['prob']=np.array(p_tr[1])
    return out 
    
def calc_ci(minimizer, maxiter=200, verbose=1, 
            prob_func=f_compare, sigmas=[0.674,0.95,0.997],
            trace_params=False):
    """
    Calculates coinfidance interval. While varying one parameter, the others
    are optimized for minimizing chi^2. With the resulting chi^2 we can 
    calculate a coinfidance for varying parameter for a given statstic e.g. 
    F-statistic
    """
    fit_params=minimizer.params
    #copy the best fit values.
    if trace_params: 
        trace={}
    org=copy_vals(fit_params)
    output=[]
    best_chi=minimizer.chisqr
    
    for para in fit_params.values():     
        if trace_params:             
            p_trace=([],[])
        if verbose:
            print 'Calculating CI for '+ para.name
        restore_vals(org,fit_params)
        step=para.stderr
        para.vary=False    
        start_val=para.value
        #minimizer.leastsq()                
        
        def calc_prob(val, offset=0.,restore=False):
            "Returns the probabilty for given Value."
            if restore: restore_vals(org,fit_params)       
            para.value=val
            minimizer.prepare_fit(para)
            minimizer.leastsq()
            out=minimizer            
            #print "calc"
            #print calc_max_chi(out.ndata, out.ndata-out.nfree,best_chi)
            prob=f_compare(out.ndata,out.ndata-out.nfree,out.chisqr,best_chi)                    
            if trace_params:                
                #print 'trace'+para.name
                p=copy_vals(out.params).values()    
                p_trace[0].append([i.value for i in out.params.values()])
                p_trace[1].append(prob)                
            return prob-offset
                        
        def search_limits(direction):
            """
            Searchs for the limits. First it looks for a upper limit and 
            then finds the sigma-limits with help of scipy root finder.
            """ 
            change=1
            old_prob=0
            i=0
            limit=start_val
            #Find a upper limit,
            while change>0.001 and old_prob<max(sigmas):
                i+=1
                limit+=step*direction
                new_prob=calc_prob(limit)
                change=new_prob-old_prob
                old_prob=new_prob
                if i>maxiter:
                    print "Reached maxiter, last val: ", limit, " with ", old_prob
                    break
                #print change, limit, old_prob
            restore_vals(org,fit_params)
            #use brentq to find sigmas.            
            
            ret = [brentq(calc_prob,start_val,limit, args=(p)) 
                    for p in sigmas if p<old_prob]            
            return ret
        
        
        upper_err=search_limits(1)
        restore_vals(org,fit_params)        
        lower_err=search_limits(-1)
        if trace_params:
            trace[para.name]=p_trace_to_dict(p_trace,fit_params)
        para.vary=True          
        output.append([para.name]+list(lower_err[::-1])+[start_val]+list(upper_err))
   
    restore_vals(org,fit_params)
    if trace_params: 
           return output, trace
    return output
    

def calc_2dmap(minimizer,x_name,y_name,nx=10,ny=10):
    best_chi=minimizer.chisqr
    org=copy_vals(minimizer.params)
    
    x=minimizer.params[x_name]
    x_upper, x_lower=x.value+3*x.stderr, x.value-5*x.stderr
    x_points=np.linspace(x_lower,x_upper,nx)
    
    y=minimizer.params[y_name]
    y_upper, y_lower=y.value+3*y.stderr, y.value-5*y.stderr
    y_points=np.linspace(y_lower,y_upper,ny)

    x.vary=False
    y.vary=False
    grid=np.dstack(np.meshgrid(x_points,y_points))

    
    def calc_prob(vals, offset=0.,restore=False):
            "Returns the probabilty for given Value."
            if restore: restore_vals(org,minimizer.params)       
            x.value=vals[0]
            y.value=vals[1]
            #minimizer.__prepared=False
            minimizer.prepare_fit([x,y])
            minimizer.leastsq()
            out=minimizer            
            
            #print "calc"
            #print calc_max_chi(out.ndata, out.ndata-out.nfree,best_chi)
            prob=f_compare(out.ndata,out.ndata-out.nfree,out.chisqr,best_chi,
                           nfix=2.)    
            return prob
    out=x_points, y_points, np.apply_along_axis(calc_prob,-1,grid)
    
    x.vary, y.vary=True, True
    restore_vals(org, minimizer.params)
    minimizer.chisqr=best_chi
    return out