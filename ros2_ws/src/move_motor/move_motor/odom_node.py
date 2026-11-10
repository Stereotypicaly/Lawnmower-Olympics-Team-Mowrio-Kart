import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

class OdomNode(Node):
    def __init__(self):
        super().__init__('odom_node')
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        
        self.v = 0.0
        self.w = 0.0
        self.time_jump = self.get_clock().now()
        
        self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.tf_broadcast = TransformBroadcaster(self)
        self.create_timer(0.05, self.update)
        
    def cmd_callback(self, msg):
        self.v = msg.linear.x;
        self.w = msg.angular.z;
        
    def update(self):
        now = self.get_clock().now()
        dt = (now - self.time_jump).nanoseconds * 1e-9
        self.time_jump = now
        
        self.yaw += self.w * dt
        self.x += self.v * math.cos(self.yaw) * dt
        self.y += self.v * math.sin(self.yaw) *dt
        qz = math.sin(self.yaw/ 2.0)
        qw = math.cos(self.yaw/2.0)
        stamp = now.to_msg()
        
        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = 'odom'
        tf.child_frame_id = 'base_link'
        tf.transform.translation.x = self.x
        tf.transform.translation.y = self.y
        tf.transform.rotation.z = qz
        tf.transform.rotation.w = qw
        self.tf_broadcast.sendTransform(tf)
        
        
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.w
        self.odom_pub.publish(odom)
        
        
def main(args=None):
    rclpy.init(args=args)
    node = OdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
            
    
if __name__ == '__main__':
    main()