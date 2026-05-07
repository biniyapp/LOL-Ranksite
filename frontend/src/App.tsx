import { useState, useEffect } from 'react'
import './App.css'

interface User {
  id: number;
  nickname: string;
  tag: string;
  score: number;
}

function App() {
  const [rankings, setRankings] = useState<User[]>([]);
  const [nickname, setNickname] = useState('');
  const [tag, setTag] = useState('');
  const [loading, setLoading] = useState(false);

  const API_URL = 'http://localhost:8000';

  const fetchRankings = async () => {
    try {
      const response = await fetch(`${API_URL}/rankings`);
      if (response.ok) {
        const data = await response.json();
        setRankings(data);
      }
    } catch (error) {
      console.error('Failed to fetch rankings:', error);
    }
  };

  useEffect(() => {
    fetchRankings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nickname || !tag) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nickname,
          tag,
        }),
      });

      if (response.ok) {
        setNickname('');
        setTag('');
        fetchRankings();
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Failed to register user'}`);
      }
    } catch (error) {
      console.error('Failed to register user:', error);
      alert('Failed to connect to backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>LoL Ranking Site</h1>
      
      <section className="registration">
        <h2>Register / Update Ranking</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Nickname (e.g. Hide on bush)"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Tag (e.g. KR1)"
            value={tag}
            onChange={(e) => setTag(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Fetching Data...' : 'Register'}
          </button>
        </form>
      </section>

      <section className="rankings">
        <h2>Ranking List</h2>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Player</th>
              <th>Score (LP)</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((user, index) => (
              <tr key={user.id}>
                <td>{index + 1}</td>
                <td>{user.nickname} <span className="tag">#{user.tag}</span></td>
                <td>{user.score}</td>
              </tr>
            ))}
            {rankings.length === 0 && (
              <tr>
                <td colSpan={3}>No rankings registered yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default App
