"""
Camera library / logger.
"""
import time
import os
import picamera

class Camera():
    """
    Camera class, which encapsulates the Raspberry Pi camera and
    tries to make it easy for an external program to just
    "take a bunch of photos as we fly"

    This isn't 100% stable so I'll drive it from camera.py for the first flight
    """
    delay = 2
    free_space_threshold = 500 * 1024 * 1024 # 500MiB

    output_directory = None
    camera_ready = False
    fail_counter = 0
    sequence = 0

    def __init__(self):
        base_directory = "/home/pi/photos/"
        os.makedirs(base_directory, exist_ok=True)
        max_index = 0
        for directory in os.listdir(base_directory):
            try:
                current = int(directory)
            except ValueError:
                continue
            if current > max_index:
                max_index = current
        directory = base_directory + str(max_index + 1)
        print("Camera: Output dir set to %s" % directory)
        try:
            os.makedirs(directory, exist_ok=True) # Python >= 3.2 required for exist_ok flag
            self.camera_ready = True
        except OSError as exception:
            print("Error while creating camera output dir: %s" % exception)
        self.output_directory = directory

    def take_photo(self):
        """
        Takes a photo and writes the resulting image to the output directory.
        Will skip taking a photo if the camera isn't ready from previous runs,
        and will detect repeat errors and disable the camera until restart.
        """
        if not self.camera_ready:
            print("Camera not ready.")
            return
        filesystem_status = os.statvfs(self.output_directory)
        free_space_bytes = filesystem_status.f_bavail * filesystem_status.f_bsize
        if free_space_bytes < self.free_space_threshold:
            print("Low on disk space: {}".format(free_space_bytes), flush=True)
            return
        self.sequence += 1
        output_file = "{0}/{1:06}.jpg".format(self.output_directory, self.sequence)
        print("Camera: taking picture to {}".format(output_file), flush=True)
        if os.path.exists(output_file):
            print("output file %s exists, skipping" % output_file)
            return
        camera = None
        try:
            camera = picamera.PiCamera()
            camera.resolution = (3280, 2464) # max resolution for v2 sensor
            camera.start_preview()
            time.sleep(self.delay)
            camera.capture(output_file)
            self.fail_counter = 0
        except Exception as exception:
            self.fail_counter += 1
            if self.fail_counter > 10:
                self.camera_ready = False
            print("Camera error, count {1}: {0}".format(exception, self.fail_counter))
            time.sleep(10) # cool off time after exception for hardware / other process to exit
        finally:
            # This turns the camera off, saving power between shots
            # It also must be run to free hardware locks for the next shot
            if camera:
                camera.close()
