# RPi/GPIO.py for development reasons, to allow for testing outside the Raspberry pi, a mock form of RPi.GPIO is required.

class MockGPIO:
    Board = 'BOARD'
    OUT = 'OUT'
    IN = 'IN'
    LOW = 0
    HIGH = 1

    @staticmethod
    def setup(pin, mode, type):
        print(f"Mock Setup: pin={pin}, mode={mode}, type={type}")

    @staticmethod
    def output(pin,state):
        print(f"Mock output: pin={pin}, state={state}")

    @staticmethod
    def input(pin):
        print(f"Mock input: pin={pin}")
        return MockGPIO.LOW
    
    @staticmethod
    def setmode(BCM):
        print(f'Mock Setmode: mode={BCM}')

    @staticmethod
    def BCM():
        print('Test')

    @staticmethod
    def PUD_UP():
        return 0

    @staticmethod
    def PUD_DOWN():
        return 1

    @staticmethod
    def cleanup():
        print("Mock cleanup")

GPIO = MockGPIO