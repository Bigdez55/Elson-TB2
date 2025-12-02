import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import EducationalDashboard from '../app/components/dashboard/EducationalDashboard';
import ModuleViewer from '../app/components/education/ModuleViewer';

const Learning: React.FC = () => {
  const location = useLocation();
  const [viewMode, setViewMode] = useState<'dashboard' | 'module'>('dashboard');
  
  useEffect(() => {
    // Check if there's a module or quiz specified in the URL
    const params = new URLSearchParams(location.search);
    if (params.has('module') || params.has('quiz')) {
      setViewMode('module');
    } else {
      setViewMode('dashboard');
    }
  }, [location]);
  
  return viewMode === 'dashboard' ? <EducationalDashboard /> : <ModuleViewer />;
};

export default Learning;