import subprocess


process = subprocess.Popen(
    ['celery', '-A', 'main', 'worker', '--pool=solo', '--loglevel=info'],
)

process_beat = subprocess.Popen(
        ['celery', '-A', 'main', 'beat', "--loglevel=info"]
)

process.wait()
process.wait()