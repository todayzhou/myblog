import time
from rq import get_current_job


def example(s):
	job = get_current_job()
	print('start the task.')
	for i in range(s):
		# 回传执行进度, meta是一个字典，可以自定义键值
		job.meta['progress'] = 100 * i/s
		job.save_meta()
		print(i)
		time.sleep(1)
	job.meta['progress'] = 100
	job.save_meta()
	print('end of tasks.')


def example1(s):
	print(s)