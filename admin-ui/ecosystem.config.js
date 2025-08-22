module.exports = {
  apps: [
    {
      name: 'linkedin-admin-ui',
      script: 'server.js',
      cwd: '/Users/burke/projects/linkedin-ingestion/admin-ui',
      instances: 1,
      exec_mode: 'fork',
      
      // Auto-restart settings
      watch: true,
      watch_delay: 1000,
      ignore_watch: ['node_modules', 'logs', '*.log'],
      
      // Process management
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '500M',
      
      // Environment
      env: {
        NODE_ENV: 'development',
        PORT: 3003,
        FASTAPI_BASE_URL: 'https://smooth-mailbox-production.up.railway.app'
      },
      
      // Logging
      log_file: 'logs/combined.log',
      out_file: 'logs/out.log',
      error_file: 'logs/error.log',
      log_date_format: 'YYYY-MM-DD HH:mm Z',
      
      // Advanced settings
      kill_timeout: 5000,
      listen_timeout: 8000,
      
      // Health monitoring
      health_check_grace_period: 3000
    }
  ],
  
  deploy: {
    production: {
      user: 'burke',
      host: 'localhost',
      ref: 'origin/master',
      repo: 'https://github.com/bautrey/linkedin-ingestion.git',
      path: '/Users/burke/projects/linkedin-ingestion',
      'pre-deploy-local': '',
      'post-deploy': 'cd admin-ui && npm install && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
}
