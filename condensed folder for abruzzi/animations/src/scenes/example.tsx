// Created: 2026-01-31
import {makeScene2D} from '@revideo/2d';
import {createRef, all, chain, waitFor} from '@revideo/core';
import {Txt, Rect, Circle, Img} from '@revideo/2d';

export default makeScene2D('example', function* (view: any) {
  const bgRef = createRef<Rect>();
  const logoContainerRef = createRef<Rect>();
  const logoRef = createRef<Img>();

  view.add(
    <>
      <Rect
        ref={bgRef}
        width={'100%'}
        height={'100%'}
        fill={'#ffffff'}
      />
      
      <Rect
        ref={logoContainerRef}
        width={100} // Increased to ensure full K icon visibility
        height={200}
        clip
        x={0}
      >
        <Img
          ref={logoRef}
          src={'/kerne-lockup.svg'}
          width={400}
          x={150} // Adjusted to center the K icon perfectly
          scale={0}
        />
      </Rect>
    </>
  );

  // Animation Sequence
  yield* chain(
    // 1. Icon pops up in center
    logoRef().scale(1, 0.6, (t) => t * t),
    waitFor(0.4),
    
    // 2. Expand and center the full logo
    all(
      logoContainerRef().width(400, 0.8),
      logoRef().x(0, 0.8),
    ),

    waitFor(2),
  );
});
