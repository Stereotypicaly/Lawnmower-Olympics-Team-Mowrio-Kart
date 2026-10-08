import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import RPi.GPIO as GPIO

# Define your GPIO pins (BCM numbering)
MOTOR_IN1 = 23 # pin 16
MOTOR_IN2 = 24 # pin 18
MOTOR_ENA = 13 # pin 33

class MotorGpioNode(Node):
    def __init__(self):
        super().__init__('motor_gpio_node')
        
        # Subscribe to /cmd_vel topic
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.listener_callback,
            10
        )
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOTOR_IN1, GPIO.OUT)
        GPIO.setup(MOTOR_IN2, GPIO.OUT)
        GPIO.setup(MOTOR_ENA, GPIO.OUT)
        
        # Setup PWM for speed control (100 Hz)
        self.pwm = GPIO.PWM(MOTOR_ENA, 100)
        self.pwm.start(0)
        
        self.get_logger().info('Motor GPIO Node has started.')

    def listener_callback(self, msg):
        linear_vel = msg.linear.x  # Forward/backward speed
        
        if linear_vel > 0:
            GPIO.output(MOTOR_IN1, GPIO.HIGH)

            GPIO.output(MOTOR_IN2, GPIO.LOW)

            duty_cycle = min(abs(linear_vel) * 50, 100) # Scale as needed

            self.pwm.ChangeDutyCycle(duty_cycle)

        elif linear_vel < 0:
            GPIO.output(MOTOR_IN1, GPIO.LOW)
            GPIO.output(MOTOR_IN2, GPIO.HIGH)
            duty_cycle = min(abs(linear_vel) * 50, 100)
            self.pwm.ChangeDutyCycle(duty_cycle)
        else:
            GPIO.output(MOTOR_IN1, GPIO.LOW)
            GPIO.output(MOTOR_IN2, GPIO.LOW)
            self.pwm.ChangeDutyCycle(0)

    def destroy_node(self):
        self.pwm.stop()
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
