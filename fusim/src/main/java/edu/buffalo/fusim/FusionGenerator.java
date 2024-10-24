/*
 * Copyright 2012 Andrew E. Bruno <aebruno2@buffalo.edu>
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy
 * of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

package edu.buffalo.fusim;

import java.util.List;

public interface FusionGenerator {
    public List<FusionGene> generate(int nFusions, int genesPerFusion);

    public void setGeneSelector(GeneSelector selector);
    public GeneSelector getGeneSelector();

    public void setGeneSelectionMethod(GeneSelectionMethod method);
    public GeneSelectionMethod getGeneSelectionMethod();

    public void setFilters(List<String[]> filters);
    public List<String[]> getFilters();
}
