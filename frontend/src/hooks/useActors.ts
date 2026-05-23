import { useState } from 'react';

export function useActors() {
  const [actorSearch, setActorSearch] = useState('');

  return { actorSearch, setActorSearch };
}
