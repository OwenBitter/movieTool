import { useEffect, useState } from 'react';
import { useStore } from '../store';
import * as api from '../api';

export function useActors() {
  const setActors = useStore((s) => s.setActors);
  const [actorSearch, setActorSearch] = useState('');

  useEffect(() => {
    api.fetchActors().then(setActors);
  }, [setActors]);

  return { actorSearch, setActorSearch };
}
