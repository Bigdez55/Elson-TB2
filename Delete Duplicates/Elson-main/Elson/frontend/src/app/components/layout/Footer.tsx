import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-800 border-t border-gray-700">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          {/* Left section */}
          <div className="flex items-center mb-4 md:mb-0">
            <span className="text-gray-400">
              © {currentYear} Trading Bot. All rights reserved.
            </span>
          </div>

          {/* Center section */}
          <div className="flex space-x-6 mb-4 md:mb-0">
            <Link to="/terms" className="text-gray-400 hover:text-white transition-colors">
              Terms of Service
            </Link>
            <Link to="/privacy" className="text-gray-400 hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <Link to="/security" className="text-gray-400 hover:text-white transition-colors">
              Security
            </Link>
          </div>

          {/* Right section */}
          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/yourusername/trading-bot"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <i className="fab fa-github text-xl"></i>
            </a>
            <a
              href="https://twitter.com/yourusername"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <i className="fab fa-twitter text-xl"></i>
            </a>
            <a
              href="https://discord.gg/yourinvite"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <i className="fab fa-discord text-xl"></i>
            </a>
          </div>
        </div>

        {/* System status */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="flex justify-between items-center text-sm">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="ml-2 text-gray-400">API Status</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="ml-2 text-gray-400">Exchange Connection</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="ml-2 text-gray-400">Data Feed</span>
              </div>
            </div>
            <Link
              to="/status"
              className="text-gray-400 hover:text-white transition-colors"
            >
              View System Status
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;