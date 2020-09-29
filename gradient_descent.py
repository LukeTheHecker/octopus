def calc_error(EOG, Cz, d):
    error = abs(pearsonr(EOG, Cz - (EOG*d))[0])
    return error

def gradient_descent(fun, EOG, Cz):
    d = random.uniform(-0.5, 0.5)
    d_mem = [d]
    stepsize = 0.005
    # print(f"initial d = {d}")
    cont = True
    cnt = 0
    while cont:
        current_error = fun(EOG, Cz, d)
        #print(f"current_error {current_error}")
        error_to_the_left = fun(EOG, Cz, d-stepsize)
        error_to_the_right = fun(EOG, Cz, d+stepsize)
        if error_to_the_left > error_to_the_right:
            d = d + stepsize
        else:
            d = d - stepsize     
        d_mem.append(d)

        if cnt > 3:
            if d_mem[-3] == d_mem [-1]:
                cont = False
        cnt += 1  
        # print(f"d changed to {d}") 
    print(cnt)
    return d
	
d_est = gradient_descent(calc_error, EOG, Cz)
print(d_est)