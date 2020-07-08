from scipy.spatial import distance




def check_points_similarity(old_points,new_points,dist_thr):
	if len(old_points.keys()) != len(new_points.keys()):
		return False
	acc_dist = 0
	for old_name,old_value in old_points.items():
		new_value = new_points[old_name]
		dist = distance.euclidean(tuple(new_value[0]),tuple(old_value[0]))
		acc_dist = acc_dist + dist
	if acc_dist < dist_thr:
		return True
	else:
		return False










	





