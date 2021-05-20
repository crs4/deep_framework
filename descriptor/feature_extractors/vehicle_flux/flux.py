import pandas
import numpy as np

class LoopArray2D:
    def __init__(self, shape, period, dtype=float, zeros=True, initial_timestamp=None):
        if zeros:
            self.array = np.zeros((shape[0], shape[1], period * 2), dtype=dtype)
        else:
            self.array = np.empty((shape[0], shape[1], period * 2), dtype=dtype)
        self.period = period
        self.loop_index = self.period
        self.last_timestamp = initial_timestamp

    def add(self, value, position):        
        self.array[position[0], position[1], self.loop_index] += value
        self.array[position[0], position[1], self.loop_index - self.period] += value
    
    def step(self):
        self.loop_index += 1
        if self.loop_index == self.period * 2:
            self.loop_index = self.period
        self.array[:, :, self.loop_index] = 0
        self.array[:, :, self.loop_index - self.period] = 0

    def get_buffer(self):
        return self.array[:, :, self.loop_index - self.period: self.loop_index]
    
    def get_sum(self):
        buffer = self.get_buffer()
        return buffer.sum(axis=2)   

    def __getitem__(self, key):
        return self.array[key] 
        
        

class Flux:
    """Implements the calculation of flux based on the location of objects tracked in a sequence of images
    """    
    def __init__(self, frame_width, frame_height, decimation=10, period=30):
        """Initialize the variables and arrays needed

        Args:
            frame_width (int): Width of the images in pixels
            frame_height (int): Height of the images in pixels
            decimation (int, optional): Segmentation factor. Defines the interval (in pixels) of the grid lines
                used to calculate the flux. Defaults to 10.
            period (int, optional): Period of time (in seconds) for calculating flux. It should be an integer 
                greater than 1. Defaults to 30.
        """        
        self.last_objects = None
        self.last_timestamp = None
        self.step_time = 0
        self.decimation = decimation
        self.frame_height = frame_height
        self.frame_width =  frame_width
        self.period = period
        # x_edges and y_edges define the 'surfaces' or grid lines over which the flux of objects is calculated
        self.x_edges = np.array(range(0, frame_width, decimation))
        self.y_edges = np.array(range(0, frame_height, decimation))
        # x_crosses and y_crosses are loop arrays used to keep count of the number of objects that cross the x_edges and y_edges
        # respectively. They are loop arrays with a length of twice the number of seconds of the period.
        self.edges_shape = (self.x_edges.shape[0], self.y_edges.shape[0])
        self.x_crosses = LoopArray2D(self.edges_shape, period)
        self.y_crosses = LoopArray2D(self.edges_shape, period)
        self.frames = 0
        self.flux = np.zeros((self.x_edges.shape[0] - 1, self.y_edges.shape[0] - 1, 2), dtype=int)
        self.locations = np.zeros_like(self.flux, dtype=int)
        grid_offset = int(decimation / 2)
        self.grid_data = {
            'x_start': grid_offset,
            'x_end': frame_width - grid_offset,
            'y_start': grid_offset,
            'y_end': frame_height - grid_offset,
            'step': decimation
        }
        self.grid = np.meshgrid(range(self.grid_data['x_start'], self.grid_data['x_end'], self.grid_data['step']), 
                                range(self.grid_data['y_start'], self.grid_data['y_end'], self.grid_data['step']), indexing='ij')

        self.x_vel = LoopArray2D(self.edges_shape, period)
        self.y_vel = LoopArray2D(self.edges_shape, period)
        self.avg_velocity = np.zeros_like(self.flux, dtype=float)
        self.obj_count = LoopArray2D(self.edges_shape, period)

        self.avg_speed = np.zeros((self.x_edges.shape[0] - 1, self.y_edges.shape[0] - 1))
        self.occupation_time = LoopArray2D(self.edges_shape, period)
        self.occupation = np.zeros_like(self.avg_speed, dtype=int)


    def update(self, objects, timestamp):
        """Compare the locatione of objects between consecutive frames and update the flux calculation

        Args:
            objects (pandas.Dataframe): Contain the centroids of the objects present in the current frame. Columns should 
                be 'x_c' and 'y_c' for horizontal and vertical coordinates of the centroids respectively. Rows 
                should be indexed with objects IDs.
            timestamp ([float]): Timestamp of the current frame in seconds 

        Raises:
            Exception: If the location of an object lies outside the frame boundaries

        Returns:
            tuple: A tuple formed by two numpy arrays: (flux_values, locations). The shape of flux_values is:
                (floor(frame_width / decimation), floor(frame_height /decimation), 2). The last dimention corrispond to the 
                horizontal and vertical component of the flux. The shape of locations is the same of flux_values but the 
                last dimention corrispond to the central point the segment used to caculate each flux value.
        """        
        if type(self.last_objects) != pandas.DataFrame:
            self.last_objects = objects
            self.last_timestamp = timestamp
            return
        
        objects_now = objects[objects.index.isin(self.last_objects.index)]
        objects_before = self.last_objects[self.last_objects.index.isin(objects.index)]

        full_segments = np.full(self.edges_shape, False, dtype=np.bool_)
        self.step_time += timestamp - self.last_timestamp
        if self.step_time >= 1:
            self.x_crosses.step()
            self.x_vel.step()
            self.y_crosses.step()
            self.y_vel.step()
            self.obj_count.step()
            self.occupation_time.step()
            self.step_time -= 1
        
        for id in objects_now.index:
            position_change_x = np.abs(objects_now.loc[id, 'x_c'] - objects_before.loc[id, 'x_c'])
            position_change_y = np.abs(objects_now.loc[id, 'y_c'] - objects_before.loc[id, 'y_c'])
            if np.hypot(position_change_x, position_change_y) > self.decimation:
                print(f'Object with id {id} is moving too fast ({(position_change_x, position_change_y)} pixels/frame) and will be ignored')
                continue
            x_cross_i = None
            x_cross_dir = 0
            y_cross_i = None
            y_cross_dir = 0

            x_edge_i_now = np.argwhere(self.x_edges < objects_now.loc[id, 'x_c']).max()
            x_edge_i_before = np.argwhere(self.x_edges < objects_before.loc[id, 'x_c']).max()
            if x_edge_i_now > x_edge_i_before:
                x_cross_i = x_edge_i_now
                x_cross_dir = 1
            elif x_edge_i_now < x_edge_i_before:
                x_cross_i = x_edge_i_before
                x_cross_dir = -1
            y_edge_i_now = np.argwhere(self.y_edges < objects_now.loc[id, 'y_c']).max()
            y_edge_i_before = np.argwhere(self.y_edges < objects_before.loc[id, 'y_c']).max()
            if y_edge_i_now > y_edge_i_before:
                y_cross_i = y_edge_i_now
                y_cross_dir = 1
            elif y_edge_i_now < y_edge_i_before:
                y_cross_i = y_edge_i_before
                y_cross_dir = -1
            if x_cross_i == 0 or y_cross_i == 0:
                raise Exception('This should not happen')
            if x_cross_i != None and y_cross_i == None:
                self.x_crosses.add(x_cross_dir, (x_cross_i - 1, y_edge_i_now))
            elif x_cross_i == None and y_cross_i != None:
                self.y_crosses.add(y_cross_dir, (x_edge_i_now, y_cross_i - 1))
            elif x_cross_i != None and y_cross_i != None:
                self.x_crosses.add(x_cross_dir, (x_cross_i - 1, y_cross_i - 1))
                self.y_crosses.add(y_cross_dir, (x_cross_i - 1, y_cross_i - 1))

            
            x_vel = (objects_now.loc[id, 'x_c'] - objects_before.loc[id, 'x_c']) / (timestamp - self.last_timestamp)
            y_vel = (objects_now.loc[id, 'y_c'] - objects_before.loc[id, 'y_c']) / (timestamp - self.last_timestamp)
            self.x_vel.add(x_vel, (x_edge_i_now, y_edge_i_now)) 
            self.y_vel.add(y_vel, (x_edge_i_now, y_edge_i_now))
            self.obj_count.add(1, (x_edge_i_now, y_edge_i_now))
            if not full_segments[x_edge_i_now, y_edge_i_now]:
                occupation_time = timestamp - self.last_timestamp
                self.occupation_time.add(occupation_time, (x_edge_i_now, y_edge_i_now))
                full_segments[x_edge_i_now, y_edge_i_now] = True

        x_crosses = self.x_crosses.get_sum()
        y_crosses = self.y_crosses.get_sum()
        self.flux = np.array(np.dstack((x_crosses, y_crosses))[:-1,:-1,:], dtype=int)

        obj_count = self.obj_count.get_sum()
        x_vel = np.nan_to_num(self.x_vel.get_sum() / obj_count)
        y_vel = np.nan_to_num(self.y_vel.get_sum() / obj_count)
        self.avg_velocity = np.dstack((x_vel, y_vel))[:-1,:-1,:]
        U, V = (self.avg_velocity[:,:,0], self.avg_velocity[:,:,1])
        self.avg_speed = np.hypot(U, V)

        self.occupation = np.array(((self.occupation_time.get_sum() / self.period * 100)[:-1,:-1]), dtype=int)
        
        # print(self.x_crosses.get_buffer(), self.y_crosses.get_buffer())
        for i, x_e in enumerate(self.x_edges):
            if i == 0:
                continue
            x = int(x_e - self.decimation / 2)
            for j, y_e in enumerate(self.y_edges):
                if j == 0:
                    continue
                y = int(y_e - self.decimation / 2)
                self.locations[i-1, j-1, :] = [x, y]
        
                    
        self.last_objects = objects
        self.last_timestamp = timestamp

        return
    
    
    
 