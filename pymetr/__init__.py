# pymetr/__init__.py

# Update the __all__ list to include specific classes you want to expose.
__all__ = ['Instrument', 'Oscilloscope', 'Subsystem', 'Acquire', 'Channel', 'Timebase', 'Trigger', 'WaveGen', 'Waveform']

try:
    from .instrument import Instrument, Subsystem  # Assuming Instrument is a class in the instruments module
    from .properties import data_property, select_property, switch_property, value_property
    from .oscilloscope import Oscilloscope  # Assuming Oscilloscope is a class in the oscilloscope module
    
    # Import all subsystem classes from subsystems.py
    from .oscilloscope_subsystems import Acquire, Channel, Timebase, Trigger, WaveGen, Waveform
except ImportError as e:
    print(f"Failed to import within pymetr: {e}")
