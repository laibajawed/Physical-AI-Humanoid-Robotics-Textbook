import React from 'react';
import OriginalLayout from '@theme-original/Layout';


export default function Layout(props: React.PropsWithChildren<{}>) {
  return (
    <>
      <OriginalLayout {...props} />

    </>
  );
}