import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class MotorNode(Node):
    def __init__(self):
        super().__init__('move_wheel_node')
        self.speed = 1.0 # m/s
        self.angle = 0.0 # rad/s
        
        self.drive_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.drive) # 10 hz
        
    def drive(self):
        msg = Twist()
        msg.linear.x = self.speed
        msg.angular.z = self.angle
        self.drive_pub.publish(msg)
        
def main(args=None):
    rclpy.init(args=args)
    node = MotorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
