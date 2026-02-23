# basic test to verify pytest is working
def inc(x):
    return x + 1

def test_answer():    
    assert inc(3) == 4
