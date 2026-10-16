import rclpy
import serial
import time
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

class RCControllerNode(Node):
    def __init__(self):
        super().__init__('rc_controller_node')
        #True = rc_mode, False = Autonomous mode
        self.rc_mode = True 
        
        #for when rc physical switch requests to stop
        self.stop_requested = True 

        #publisher for stop request
        self.stop_pub = self.create_publisher(Bool, '/stop_requested', 1)

        #publisher for modes
        self.mode_pub = self.create_publisher(Bool, '/robot_mode', 1)

        #publisher for rc velocity, queue size 1
        self.pub = self.create_publisher(Twist,'/cmd_vel', 1)

        #joystick values
        self.rcThrottle = 0.0 
        self.rcSteering = 0.0

        self.max_linear_speed = 0.5 #m/s
        self.max_angular_speed = 1.0 #rad/s or ~57 deg/s

        #setup arduino serial connection
        try:
            self.arduino = serial.Serial(
                '/dev/serial/by-id/usb-Arduino_Srl_Arduino_Uno_7563331313335131A1B0-if00',
                9600,
                timeout=0
                )
        except serial.SerialException as error:
            self.arduino = None
            self.get_logger().error(f"arduino connection failed: {error}")

        self.serial_buffer = bytearray() #buffer when receiving serial commands
        self.last_valid_arduino_time = None #to detect if usb disconnected

        #every 0.1 sec, the timer will call the publish command function
        self.timer = self.create_timer(0.1, self.publish_command)

    def read_arduino(self):
        #if arduino connection was established
        if self.arduino is not None:
            #number of bytes waiting to be read
            available = self.arduino.in_waiting

            if available > 0:
                data = self.arduino.read(available)
                self.serial_buffer.extend(data)
                
                #while '\n" is in the byte sequence
                while b'\n' in self.serial_buffer:
                    #seperate the buffer by '\n, line is a full serial reading
                    line, separator, remaining = self.serial_buffer.partition(b'\n')
                    self.serial_buffer = bytearray(remaining) 
                    
                    #serial byte sequence to string
                    text = line.decode('utf-8', errors='replace').strip()
                    self.get_logger().info(f'Arduino: {text}')
                    parts = text.split(' | ') #split line and create a list

                    if len(parts) != 5: #complete message check
                        self.stop_requested = True
                        self.get_logger().warning('Incomplete Arduino message')
                        continue
                    
                    try:
                        mode = int(parts[0].split(': ')[1])
                        stop = int(parts[1].split(': ')[1])
                        steering = int(parts[2].split(': ')[1])
                        throttle = int(parts[3].split(': ')[1])
                        arduino_stop_requested = int(parts[4].split(': ')[1])
                        
                    except(ValueError, IndexError):
                        self.stop_requested = True
                        self.get_logger().warning('Invalid arduino mode value')
                        continue

                    #check all receiver pulse widths, normal range (1100-1900)
                    if not all(900 <= value <= 2100 for value in (mode, stop, steering, throttle)):
                        self.stop_requested = True
                        self.get_logger().warning('invalid receiver signal')
                        continue
                    
                    if arduino_stop_requested not in (0, 1):
                        self.stop_requested = True
                        self.get_logger().warning('invalid stop request')
                        continue

                    #read time after commancds are checked
                    self.last_valid_arduino_time = time.monotonic()

                    #assign arduino values to ros2 values
                    self.stop_requested = bool(arduino_stop_requested) or (stop < 1500)
                    self.rc_mode = (mode < 1500) #true if arduino sends ~1100
                    #(arduino reading - center) / (extremes - center)
                    #this is done to normalize values to -1 through +1
                    self.rcThrottle = (throttle - 1524) / 400
                    self.rcSteering = (steering - 1500) / 400
                    

    def publish_command(self):#runs every 0.1 sec according to the timer in __init__

        #detect communication error
        try:
            self.read_arduino()
        except (serial.SerialException, OSError) as error:
            self.get_logger().error(f"Arduindo communication lost: {error}")
            self.arduino = None
            self.stop_requested = True
            self.rcThrottle = 0.0
            self.rcSteering = 0.0

        #detects missing data, publish_command runs every 0.1 seconds
        if(self.last_valid_arduino_time is None or time.monotonic() - self.last_valid_arduino_time > 0.5):
            self.stop_requested = True
            self.rcThrottle = 0.0
            self.rcSteering = 0.0
        
        msg = Twist() #velocity commands
        mode_msg = Bool()
        stop_msg = Bool()

        #set rc mode and publish
        mode_msg.data = self.rc_mode
        self.mode_pub.publish(mode_msg)

        #set stop_requested msg and publish
        stop_msg.data = self.stop_requested
        self.stop_pub.publish(stop_msg)

        #set limits to the joystick throttle and steering
        rcThrottle = max(-1.0, min(1.0, self.rcThrottle))
        rcSteering = max(-1.0, min(1.0, self.rcSteering))

        #joystick dead zones for unintentional small inputs
        if abs(rcThrottle) < 0.05:
            rcThrottle = 0.0
        if abs(rcSteering) < 0.05:
            rcSteering = 0.0
        
        #set Twist msg values and publish to topic
        msg.linear.x = rcThrottle * self.max_linear_speed #set velocity
        msg.angular.z = rcSteering *self.max_angular_speed #set angular vel

        #stop robot when switch C is 1 or when switch F is 0(auto-mode)
        #or stop_requested is triggered in another way
        if self.stop_requested or not self.rc_mode:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        if self.rc_mode:
            self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = RCControllerNode()

    try:
        #keeps node running on a loop to execute timer commands continuously
        rclpy.spin(node) 
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown() #shutdown ROS2

if __name__ == '__main__':
    main()

