import { useState, useEffect } from 'react';
import { getPlugins } from './services/api';
import ChatWidget from './components/ChatWidget';
import './App.css';

export default function App() {
  const [plugins, setPlugins] = useState([]);
  const [selectedPlugin, setSelectedPlugin] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const response = await getPlugins();
        setPlugins(response.data.plugins);
        if (response.data.plugins.length > 0) {
          setSelectedPlugin(response.data.plugins[0].id);
        }
      } catch (err) {
        setError('Failed to load plugins');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPlugins();
  }, []);

  if (loading) return null;
  if (error) return null;

  return (
    <ChatWidget
      plugins={plugins}
      selectedPlugin={selectedPlugin}
      onPluginChange={setSelectedPlugin}
    />
  );
}
