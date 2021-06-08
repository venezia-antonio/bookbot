#!/usr/bin/env python3

import rospy
import math
import actionlib

from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib_msgs.msg import GoalStatus
from geometry_msgs.msg import Pose, Point, Quaternion
from tf.transformations import quaternion_from_euler
from gazebo_msgs.srv import SpawnModel
from gazebo_msgs.srv import GetModelState


class MoveBaseSeq():

    def __init__(self):
        self.model_coordinates = rospy.ServiceProxy( '/gazebo/get_model_state', GetModelState)
        rospy.wait_for_service("/gazebo/spawn_sdf_model")
        rospy.init_node('move_base_sequence')
        points_seq = rospy.get_param('move_base/p_seq')
        yaweulerangles_seq = rospy.get_param('move_base/yea_seq')
        quat_seq = list()
        self.pose_seq = list()
        self.goal_cnt = 0
        for yawangle in yaweulerangles_seq:
            quat_seq.append(Quaternion(*(quaternion_from_euler(0, 0, yawangle*math.pi/180, axes='sxyz'))))
        n = 3
        points = [points_seq[i:i+n] for i in range(0, len(points_seq), n)]
        for point in points:
            self.pose_seq.append(Pose(Point(*point),quat_seq[n-3]))
            n += 1
        self.client = actionlib.SimpleActionClient('move_base',MoveBaseAction)
        rospy.loginfo("Waiting for move_base action server...")
        wait = self.client.wait_for_server(rospy.Duration(5.0))
        if not wait:
            rospy.logerr("Action server not available!")
            rospy.signal_shutdown("Action server not available!")
            return
        rospy.loginfo("Connected to move base server")
        rospy.loginfo("Starting goals achievements ...")
        self.movebase_client()

    def active_cb(self):
        rospy.loginfo("Goal pose "+str(self.goal_cnt+1)+" is now being processed by the Action Server...")

    def feedback_cb(self, feedback):
        rospy.loginfo("Feedback for goal pose "+str(self.goal_cnt+1)+" received")

    def done_cb(self, status, result):
        self.goal_cnt += 1

        if status == 2:
            rospy.loginfo("Goal pose "+str(self.goal_cnt)+" received a cancel request after it started executing, completed execution!")

        if status == 3:
            rospy.loginfo("Goal pose "+str(self.goal_cnt)+" reached") 
            rospy.sleep(1)
            # Books spawning
            spawn_model_client = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
            if self.goal_cnt == 1:
                self.object_coordinates = self.model_coordinates("mybot", "")
                y = self.object_coordinates.pose.position.y
                x = self.object_coordinates.pose.position.x
                spawn_model_client('book1', open("/home/ivano/catkin_ws/src/bookbot/models/aws_robomaker_retail_BookE_01/model.sdf",'r').read(), "/", Pose(position = Point(x,y,0.95), orientation = Quaternion(0,0,0,1)),"world")
            if self.goal_cnt == 2:
                self.object_coordinates = self.model_coordinates("mybot", "")
                y = self.object_coordinates.pose.position.y
                x = self.object_coordinates.pose.position.x
                spawn_model_client('book2', open("/home/ivano/catkin_ws/src/bookbot/models/aws_robomaker_retail_BookE_01/model.sdf",'r').read(), "/", Pose(position = Point(x,y,0.95), orientation = Quaternion(0,0,0,1)),"world")
            if self.goal_cnt == 3:
                self.object_coordinates = self.model_coordinates("mybot", "")
                y = self.object_coordinates.pose.position.y
                x = self.object_coordinates.pose.position.x
                spawn_model_client('book3', open("/home/ivano/catkin_ws/src/bookbot/models/aws_robomaker_retail_BookE_01/model.sdf",'r').read(), "/", Pose(position = Point(x,y,0.5), orientation = Quaternion(0,0,0,1)),"world")
           
            if self.goal_cnt < len(self.pose_seq):
                next_goal = MoveBaseGoal()
                next_goal.target_pose.header.frame_id = "map"
                next_goal.target_pose.header.stamp = rospy.Time.now()
                next_goal.target_pose.pose = self.pose_seq[self.goal_cnt]
                print(self.pose_seq[self.goal_cnt])
                rospy.loginfo("Sending goal pose "+str(self.goal_cnt+1)+" to Action Server")
                rospy.loginfo(str(self.pose_seq[self.goal_cnt]))
                self.client.send_goal(next_goal, self.done_cb, self.active_cb, self.feedback_cb) 
            else:
                rospy.loginfo("Final goal pose reached!")
                rospy.signal_shutdown("Final goal pose reached!")
                return

        if status == 4:
            rospy.loginfo("Goal pose "+str(self.goal_cnt)+" was aborted by the Action Server")
            rospy.signal_shutdown("Goal pose "+str(self.goal_cnt)+" aborted, shutting down!")
            return

        if status == 5:
            rospy.loginfo("Goal pose "+str(self.goal_cnt)+" has been rejected by the Action Server")
            rospy.signal_shutdown("Goal pose "+str(self.goal_cnt)+" rejected, shutting down!")
            return

        if status == 8:
            rospy.loginfo("Goal pose "+str(self.goal_cnt)+" received a cancel request before it started executing, successfully cancelled!")

    def movebase_client(self):
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now() 
        goal.target_pose.pose = self.pose_seq[self.goal_cnt]
        rospy.loginfo("Sending goal pose "+str(self.goal_cnt+1)+" to Action Server")
        rospy.loginfo(str(self.pose_seq[self.goal_cnt]))
        self.client.send_goal(goal, self.done_cb, self.active_cb, self.feedback_cb)
        rospy.spin()

if __name__ == '__main__':
    try:
        MoveBaseSeq()
    except rospy.ROSInterruptException:
        rospy.loginfo("Navigation finished.")
