import React, { useEffect, useState } from 'react';
import { useAppState } from '../context/AppContext';
import * as api from '../api';

export function useActors() {
  const { state, dispatch } = useAppState();
  const [actorSearch, setActorSearch] = useState('');

  useEffect(() => {
    api.fetchActors().then((actors) => {
      dispatch({ type: 'SET_ACTORS', actors });
    });
  }, [dispatch]);

  return { actorSearch, setActorSearch };
}
