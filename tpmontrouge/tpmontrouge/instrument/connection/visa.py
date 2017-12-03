try:
    from ._visa import *
    from ._visa import pyvisa as visa    

except ImportError:
    def open_resource(*args, **kwd):
        raise Exception('Visa not installed on your computer') 
    visa = None

