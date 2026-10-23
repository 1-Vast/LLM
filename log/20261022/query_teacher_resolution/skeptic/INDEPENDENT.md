# Independent teacher resolution: bounded reachability, honest outer derivative

2026-10-22. Readmandatoryobjective and update_rule_renewal DECISION/CONTINUATION; no currentpeer draft read. PrewrotePROTOCOL then ran numpy fixed-state skepticalcheck; CHECK.json+codehash retained. No networkrequest, biologicaldata/labels, weights or reserve. No trainingdistributionchosen to makeateacherwin. Verdict: support a bounded operationverification only; wholemethod noveltystillUNRESOLVED, no biologicalpilot/corepromotion.

## Local target stop-gradient is not an outer stop-gradient

The intended A_new=A+eta_A*r(P,k,u,b)*e*kT is a differentiable functionofP. If u_target=detach(u+r*e) is literally built insidean autodiffgraph and then usedto form A−eta*grad_A .5||Ak−u_target||² with create_graph, its Pdependencyisgone. Queryloss then has zero derivative through thatteacher, contraryto the claimedexternalquerytraining. A trainableinitialA/b or anotherPpath couldstillreceivegradients, so 'someparametertrained' wouldnotcertifyPistrained.

There is a lawful preciseimplementation: take the INNERpartialgradient while treating localtargetconstant, simplify the resultingstateupdate to A_new=A+eta*r*e*kT, and DIFFERENTIATEthatupdatewithrespecttoP in theOUTERobjective. This is a specifiedtwo-levelderivative convention/customrule, not simultaneouslydetachingtargetthroughalllevels. Directexplicitupdate (or equivalentcustomVJP) implementsit without claiming stop_gradientmagicallyreopensitsgraph. Mustdefine whatpaths throughu,b,e and earlierupdates arekept; truncatingthem givesa differentlearningalgorithm. Query-derivedgradient isnot anextraassaymeasurement.

Ourfixednonorthogonalquerycheck analyticallydifferentiatesallPentries and comparescentralfinitedifferences: maxerror4.99e−13, nonzerogradientnorm.00362866. It verifies intendedexplicitouterpath, not anautodifflibraryimplementation/fullmulti-stepgradient. Fulltargetdetachwoulderase thatpath. No algorithmicnoveltyisclaimedforthisstandardbileveldistinction.

## One support key severely constrains WHERE adaptation propagates

For fixedkeyk_s, DeltaA=eta*e*r*k_sT has rank≤1 and DeltaA*k_q=eta*e*r*(k_sT*k_q). Thus theteacher chooses thehiddenvectorbut cannot choose a query-specificrightfactor beyond keygeometry. With fixedb and k_qorthogonaltoallobservedsupportkeys, thequeryprediction is EXACTLYunchanged, foranyP/eta/nonlinearitytanh, not merelyfirstorder. With multipleupdates, DeltaA is a sumofouterproducts withrightfactors in span(supportkeys), so A restricted to thatspan'sorthogonalcomplement staysunchanged. This is a reachable-subspacerestriction, not aninformationimpossibilitytheorem for alllearnedoptimizers.

Theexecutedorthogonal2Dcheck usesfour teacherPchoices, includingzero,negatedandscaledP; allqueryoutputs identically−.35838770503. Enabling the proposedbupdate changes theorthogonalqueryby−.00247528853, exactlythe ordinaryhead-onlyterm; theteacherP has noinfluenceonthatsingle-stepheadupdate because theformula usespreupdateh. Do not creditthisheadchannelas evidence of learnedhiddenpropagation. On latersteps P can alterpastmodels/supporthiddenstates and therebylaterbupdates, so totalmultisteppredictioninvariance doesNOTfollowwhenbisadaptive; theexactinvarianceisintheAactiononorthogonalkeys. Thisscope avoids anoverstrongrank-oneveto.

Rankoneitselfdoesnotmean weak: ordinarySGDon a singleexampleA-layer alsohasrightfactork_s. Theteacher can select a hiddenvectoroutside the ordinarybackpropvector b⊙tanh'(u), potentiallybypassing saturation. That is a realhypothesis requiringfairtraining, not a provedbenefit. StaticSGM can also producearbitraryactivationgradient; the2020primaryalreadyhasthatpropertyandfrozentransfer. Ordinarylearnedoptimizerwithpreconditioningcouldchangetherightfactorandgeometry, but mustpayforitsstate/metatraining anduseexactlythe same keys/labels; don't give itafreequeryspecificfuturetruth.

## Representation requirement for drugcontexts

If keysareonehotorthogonaldrugidentities, a feedback ononedrug cannotchange thehiddenrepresentationofanotherunmeasuredorthogonaldrugviaA. Anyfunctionalimprovementthencomesfromoutputhead, pretrainedsharedfeatures, or laterindirectmultistepchannels. Claiming powerfulcrossdrughiddenupdating wouldthereforeneed a sourcelearnedembedding with legallypredictiveinterventionrelations, or anexplicitdifferentupdategeometry. Addingarbitraryembeddings isnot itselfa newcore; thoseembeddingsmustbeavailable to ordinarycontrols. Normalizedsharedkeysimilaritycantransmitanuisancecorrelationtoo; itisnot acertificateofcellbiology.

Ateacherthatlearns r fromsourcequeryrisk may helpthehiddenupdatechoosewhichresponsesareuseful withinthereachablesubspace. The operative question is whether querytraining learns a better transferablevector than gradientimitation/truncatedbackprop orlearnedoptimizer trainingunderthesamecontext/compute—not whether thesamevectorcanbecalled atargetorgradient. This actualdistinctionisnotresolvedbytheabovegeometricidentity.

## Traceable ordinary comparisons and what they would falsify

A documentedstaticSGM trainedagainsttruebackpropactivationgradients (rootpreviousauthenticated2009.09675v1methods3.2/3.3) is a traceablemechanism. Comparea matchedteacherarchitecture suppliedthesameinputinformation andsourceepisodes, withits gradientimitationobjective, to theexternalqueryteacher. Matchbackpropteacherlabelcompute, outerquerytraining, validationbudget anddeploymentsteps. This tests a trainingobjectiveeffect; itdoesnotprove nootherpublishedlearnedoptimizeralreadyusesqueryrisk.

A traceableMAML/learnedoptimizer family usesheldoutqueryrisk totrainupdates, but merelyinvokingitsfamilydoesnotprovethepreciseP-conditionedfactorizationisold. A faithfulimplementationwiththesamefactorizationandouterriskconstructedbyusis a parameterizationcontrol, not priordiscoveryevidence. ThewholemethodpriorartremainsUNRESOLVED on currentauthenticatedsources. Samefixedpredictor/sourceepisode head-onlyadaptation andcompute-matchedSGD/refit are functionalcontrols. A directfullsource-trainedpredictorwithoutadaptivefeedbacktests whetherfeedback updatingisneeded; even teacherutilitydoesnotdemonstrateagentorRSInecessity.

Minimumfalsifiernowchangesfrom'compare samecode twice' to checking two independentaxes: first verify actualouterPgradient and reachablequerytransfer; then, if a genuinefunctionalcontract andnontrivialcomputationalreasonexist, comparequery-trained versusgradient-imitationteachers underbalancedsource/deploymentcost. Do NOT launchasolvedoldALMANAC/CDKconfigurationorbignewbiologicalpilotmerelytoseekteacherwins. Noactualfiniteperformanceincrement,newrepresentation ortechnicalpropertyhasbeenestablishedyet.

## Decision

SUPPORTED analytic reachabilityrestriction and intendedoutergradientverification in fixedartificialexamples. STOP only a literal fulltarget-detach implementation claimingPquerytraining and anyone-stepclaimofteacher-controlledhiddeneffectonorthogonalkeys; allowactualexplicitmetaupdateverification. Wholeexternalqueryteachermechanism remainsUNRESOLVED/NO_PROMOTION, notrefutedbyfamilymembership/rankonealone andnotnovelmerelybecauseitspriorartisunfinished. No newupdatevariant isproposedhere. FullWM/agent/inheritance/joint/improvedimproverobjective remainsnotachieved.
