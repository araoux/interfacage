import os

import pyqtgraph as pg
from time import sleep
from pyqtgraph.Qt import QtCore, QtGui


def _infinite_range():
    i = 0
    while True:
        yield i
        i += 1

class Iterator(object):
    def __init__(self, parent):
        self._first = True
        self.reset_iterator()
        self._parent = parent

    def reset_iterator(self):
        self._iterator = iter([])

    def configure_iterator(self, list_of_elm=None):
        if list_of_elm is None:
            self._iterator = iter(_infinite_range())
        else:
            self._iterator = iter(list_of_elm)

    def __iter__(self):
        return self

    def next(self):
        if self._first:
            self._first = False
        else:
            self._parent.end_of_one_iteration.emit(None)
        next_ = next(self._iterator)
        return self._parent.what_to_do(next_)

    def __next__(self):
        return self.next()


class ExpThread(pg.QtCore.QThread):
    """ Thread used to loop over an experiment

    This class is started from the StartStopButton object. 
    You need to specify the attribute exp with an experiment instance. 

    Basically, this will start a loop of the experiment with the possibility to stop or pause the loop. 

    Usually, you will subclass this class and specify the exp attribute or property and the get_iterator method. 

    IMPORTANT NOTE : for matplotlib, the plot should be done in the experiment thread. For PyQT graph, it
    should be done in the main thread. The end_of_one_iteration signal is used for the plot. 

    """
    running_exp = None
    end_of_one_iteration = pg.QtCore.Signal(object)
    def __init__(self, parent_windows=None, **kwd):
        self.parent_windows = parent_windows
        self.btn = parent_windows.start_stop_buttons
        self.iterator = Iterator(parent=self)
        super(ExpThread, self).__init__()
        self.end_of_one_iteration.connect(parent_windows.end_of_one_iteration)

    def run(self):
        self.running_exp = self.exp
        self.running_exp.loop(self.iterator)
        self.btn.stop()

    def get_iterator(self):
        return None

    def start(self):
        self.iterator.configure_iterator(self.get_iterator())
        super(ExpThread, self).start()

    def what_to_do(self, next):
        while True:
            if self.btn.get_state()=='Running':
                return next
            if self.btn.get_state()=='Stopped' or self.btn.get_state()=='WaitingForStop':
                raise StopIteration
            sleep(.05)

    def save(self, filename):
        try:
            self.running_exp.save(filename)
        except AttributeError:
            raise Exception('In order to save, the experiment should have a save method')

class StateMachine(pg.QtCore.QObject):
    sig_new_state = pg.QtCore.Signal(str)
    previous_state = None
    state = None
    def __init__(self, states, initial_state=None, *args, **kwd):
        super(StateMachine, self).__init__(*args, **kwd)
        self._states = states
        if initial_state is None:
            initial_state = states[0]
        self.set_state(initial_state)
        self.sig_new_state.connect(self.entering)

    def set_state(self, state):
        if state not in self._states:
            raise Exception('State not allowed')
#        print('SET STATE', state)
        self.previous_state = self.state
        self.state = state
        self.sig_new_state.emit(state)
#        self.sig_new_state.connect(self.entering)

    def get_state(self):
        return self.state

    def entering(self, value):
        methode = getattr(self, 'entering_'+value.lower(), None)
        if methode is not None:
            methode(self.previous_state)
        
    def connect(self, *args, **kwd):
        self.sig_new_state.connect(*args, **kwd)

class StartStopPause(StateMachine):
#    _thread_class = None
#    new_state = pg.QtCore.Signal(str)
    def __init__(self, layout=None, thread_class=None, *args, **kwd):
        super(StartStopPause, self).__init__(states=['Stopped', 'Paused', 'Running', 'WaitingForStop'], *args, **kwd)
        on_off_btn = pg.QtGui.QPushButton("Start")
        on_off_btn.clicked.connect(self.start_stop)
        self.on_off_btn = on_off_btn
        pause_btn = pg.QtGui.QPushButton("Pause")
        pause_btn.clicked.connect(self.pause_resume)
        pause_btn.setEnabled(False)
        self.pause_btn = pause_btn
        if layout is not None:
            layout.addWidget(self.on_off_btn)
            layout.addWidget(self.pause_btn)
        self.set_state('Stopped')

    def start_thread(self):
        assert self._thread_class is not None, 'You should set the thread_class'
        self._thread = self._thread_class(btn=self)
        self._thread.start()
        

    def start(self):
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText('Pause')
        self.on_off_btn.setText('Stop')
        self.start_thread()
        self.set_state("Running")

    def ask_stop(self):
        self.pause_btn.setEnabled(False)
        self.on_off_btn.setEnabled(False)
        self.set_state('WaitingForStop')

    def stop(self):
        self.pause_btn.setText('Pause')
        self.pause_btn.setEnabled(False)
        self.on_off_btn.setText('Start')
        self.on_off_btn.setEnabled(True)    
        self.set_state('Stopped')

    def start_stop(self):
        if self.on_off_btn.text()=='Start':
            self.start()
        else:
            self.ask_stop()            

    def pause_resume(self):
        if self.pause_btn.text()=='Resume':
            self.pause_btn.setText('Pause')
            self.set_state("Running")
        else:
            self.pause_btn.setText('Resume')
            self.set_state("Paused")
    
class StartStopPauseSave(StartStopPause):
    def __init__(self, layout=None, thread_class=None, *args, **kwd):
        super(StartStopPauseSave, self).__init__(layout, thread_class, *args, **kwd)
        save_btn = pg.QtGui.QPushButton("Save")
        save_btn.setEnabled(False)
        self.save_btn = save_btn
        if layout is not None:
            layout.addWidget(self.save_btn)
        self.connect(self.new_state_save)
        self.save_btn.clicked.connect(self.save_gui)


    _initial_dir = os.getenv('HOME') or ''
    def save_gui(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self.save_btn, 'Save file', 
                        self._initial_dir, "Data file (*.txt)")
        if isinstance(file_name, tuple): # depends on the version ...
            file_name = file_name[0]
        if file_name:
            self.save(file_name)

    def save(self, filename):
        self._thread.save(filename)

    def new_state_save(self, state):
        if state=='Running':
            self.save_btn.setEnabled(False)
        elif state=='Paused':
            self.save_btn.setEnabled(True)
        elif state=='Stopped':
            if self._thread.running_exp is not None:
                self.save_btn.setEnabled(True)
            else:
                self.save_btn.setEnabled(False)


class StartStopPauseSaveSingle(StartStopPauseSave):
    def __init__(self, layout=None, thread_class=None, *args, **kwd):
        super(StartStopPauseSaveSingle, self).__init__(layout, thread_class, *args, **kwd)
        single_btn = pg.QtGui.QPushButton("Single")
        single_btn.setEnabled(True)
        self.single_btn = single_btn
        if layout is not None:
            layout.addWidget(self.single_btn)
        self.connect(self.new_state_single)
        self.single_btn.clicked.connect(self.single_clicked)


    def single_clicked(self):
        self.start_single()

    def new_state_single(self, state):
        if state=='Running':
            self.single_btn.setEnabled(False)
        elif state=='Paused':
            self.single_btn.setEnabled(True)
        elif state=='Stopped':
            self.single_btn.setEnabled(True)


    def start_single_thread(self):
        assert self._thread_class is not None, 'You should set the thread_class'
        self._thread = self._thread_class(btn=self, single=True)
        self._thread.start()
        

    def start_single(self):
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText('Pause')
        self.on_off_btn.setText('Stop')
        self.start_single_thread()
        self.set_state("Running")

