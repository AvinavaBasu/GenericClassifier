class Config:
    def __init__(self, env):
        self.host = {
            'dev': 'internal-dev-gc-application-lb-1377632991.us-east-1.elb.amazonaws.com:8080',
            'uat': 'internal-acceptance-gc-application-lb-2076132661.us-east-1.elb.amazonaws.com:8080',
            'local': '192.168.75.70:9081',
            'prod': 'internal-prod-gc-application-lb-1211665679.us-east-1.elb.amazonaws.com:8080'
        }[env]

        self.tls = {
            'dev': 'http',
            'uat': 'http',
            'local': 'http',
            'prod': 'http',
        }[env]
