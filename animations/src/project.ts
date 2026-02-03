// Created: 2026-01-31
import {makeProject} from '@revideo/core';
import example from './scenes/example?scene';
import defillama from './scenes/defillama?scene';

export default makeProject({
  scenes: [defillama, example],
});
