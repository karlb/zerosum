from setuptools import setup

setup(name='Zerosum',
      version='1.0',
      description='Track your owes',
      author='Karl Bartel',
      author_email='karl42@gmail.com',
      url='https://www.python.org/community/sigs/current/distutils-sig',
      install_requires=['Flask>=0.7.2', 'MarkupSafe', 'psycopg2', 'flask-login', 'pytz', 'sendgrid'],
     )
