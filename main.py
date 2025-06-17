import ctypes
from ctypes import wintypes
from multiprocessing import shared_memory
import numpy as np
import cv2
import json

# Define the shared frame structure
class VideoFrameData(ctypes.Structure):
    _fields_ = [
        ("lock", ctypes.c_long), #not used
        ("width", ctypes.c_uint),
        ("height", ctypes.c_uint),
        ("data", ctypes.c_char * (1920 * 1080 * 3)),
    ]


def get_image(shm_name:str, image_band_num: int):
    #get shared memory
    shm = shared_memory.SharedMemory(name=shm_name)
    buffer_address = ctypes.addressof(ctypes.c_char.from_buffer(shm.buf))
    # Pointer to entire struct
    frame_ptr = ctypes.cast(buffer_address, ctypes.POINTER(VideoFrameData))
    frame = frame_ptr.contents
    #create numpy array from the image buffer frame.data
    NumColors = image_band_num
    valid_size = frame.width * frame.height * NumColors
    np_array = np.frombuffer(frame.data, dtype=np.uint8)
    np_image= np_array[:valid_size].reshape((frame.height, frame.width, NumColors))
    np_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)    
    np_image = np.fliplr(np_image)

    cv2.imwrite("test.png", np_image)
    


if "__main__" == __name__:
    # Load kernel32.dll
    kernel32 = ctypes.windll.kernel32

    # Define function signatures
    _CreateMutex = kernel32.CreateMutexW
    _CreateMutex.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR]
    _CreateMutex.restype = wintypes.HANDLE

    _WaitForSingleObject = kernel32.WaitForSingleObject
    _WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _WaitForSingleObject.restype = wintypes.DWORD

    _ReleaseMutex = kernel32.ReleaseMutex
    _ReleaseMutex.argtypes = [wintypes.HANDLE]
    _ReleaseMutex.restype = wintypes.BOOL

    _CloseHandle = kernel32.CloseHandle
    _CloseHandle.argtypes = [wintypes.HANDLE]
    _CloseHandle.restype = wintypes.BOOL

    #read json configuration
    with open("config.json") as configuration:
        config = json.load(configuration)

    # Example usage
    mutex_name = config["MutexName"]
    mutex_handle = _CreateMutex(None, False, mutex_name)

    if mutex_handle:
        while True:  # Retry loop
            result = _WaitForSingleObject(mutex_handle, 5000)  # Wait 5 seconds
            if result == 0:  # WAIT_OBJECT_0 (mutex acquired)
                print("Mutex acquired")
                try:
                    get_image(shm_name= config["SharedMemoryName"], image_band_num= config["ImageBandNumber"])
                finally:
                    if not _ReleaseMutex(mutex_handle):
                        print("Failed to release mutex:", ctypes.get_last_error())
                    else:
                        print("Mutex released")
                break  # Exit loop after successful acquisition and processing
            elif result == 0x102:  # WAIT_TIMEOUT (0x102 in hex)
                print("Mutex acquisition timed out after 5 seconds, retrying...")
                continue  # Retry
            else:  # Other errors (e.g., WAIT_FAILED)
                print("Failed to acquire mutex:", ctypes.get_last_error())
                break  # Exit on error

        if not _CloseHandle(mutex_handle):
            print("Failed to close mutex handle:", ctypes.get_last_error())
    else:
        print("Failed to create mutex:", ctypes.get_last_error())
    


    
