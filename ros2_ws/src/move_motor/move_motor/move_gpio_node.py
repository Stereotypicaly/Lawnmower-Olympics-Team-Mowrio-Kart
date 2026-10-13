import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import RPi.GPIO as GPIO

# LEFT WHEEL
MOTOR_IN1_L = 23 # pin 16
MOTOR_IN2_L = 24 # pin 18
MOTOR_ENA_L = 13 # pin 33

# RIGHT WHEEL
MOTOR_IN1_R = 27 # pin 13 red
MOTOR_IN2_R = 17 # pin 11 black 
MOTOR_ENA_R = 12 # pin 32 gold

MAX_SPEED = 2.0 # m/s that maps to duty cycle. TUNE THIS

class MotorGpioNode(Node):
    def __init__(self):
        super().__init__('motor_gpio_node')
        
        self.wheel_base = 0.254 # meters
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        
        # H BRIDGE
        for pin in (MOTOR_IN1_L, MOTOR_IN2_L, MOTOR_ENA_L, MOTOR_IN1_R, MOTOR_IN2_R, MOTOR_ENA_R):
            GPIO.setup(pin, GPIO.OUT)

        
        # Setup PWM for speed control (100 Hz)
        self.pwm_l = GPIO.PWM(MOTOR_ENA_L, 100)
        self.pwm_r = GPIO.PWM(MOTOR_ENA_R, 100)
        self.pwm_l.start(0)
        self.pwm_r.start(0)
        
        # Subscribe to /cmd_vel topic
        self.drive_sub = self.create_subscription(Twist, '/cmd_vel', self.listener_callback, 10)
        
        self.get_logger().info('Motor GPIO Node has started.')

    def set_wheel(self, in1, in2, pwm, vel):
        if vel > 0:
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
        elif vel <0:
            GPIO.output(in2, GPIO.HIGH)
            GPIO.output(in1, GPIO.LOW)
        else:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)
        pwm.ChangeDutyCycle(min(abs(vel) / MAX_SPEED * 100.0, 100.0))

    def listener_callback(self, msg):
        linear = msg.linear.x
        angular = msg. angular.z
        
        
        left = linear - angular * self.wheel_base / 2
        right = linear + angular * self.wheel_base / 2
        
        self.set_wheel(MOTOR_IN1_L, MOTOR_IN2_L, self.pwm_l, left)
        self.set_wheel(MOTOR_IN1_R, MOTOR_IN2_R, self.pwm_r, right)

    def destroy_node(self):
        self.pwm_l.stop()
        self.pwm_r.stop()
        GPIO.cleanup()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MotorGpioNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
