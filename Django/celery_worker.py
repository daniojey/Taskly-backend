import subprocess


process = subprocess.Popen(
    ['celery', '-A', 'main', 'worker', '--pool=solo'],
)

process.wait()