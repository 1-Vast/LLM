仅审查以下两项争议，回答不超过1000中文字符，不要展开逐行源码、不编造bug。先前审查有多次自我撤回且length截断，不能视为已通过。
1. 审查称final只有rho0造成4332fits。但selected按family逐一选，实际family是rho_0/rho_0.5/rho_1/direct/no_rna/four_gene/rbf/refit八个，final三rho各2=6,四direct各1=4,七dev refit各3=21, null3。base1806+source2496+final31+null3=4336。已对同一未改run代码执行完整24source/7dev/64config synthetic smoke，devHigh都NaN，实际receipt如下。是否撤回错误4332判断？
{"status": "PREDICTIONS_COMPLETE_UNSCORED", "estimator_fits": 4336, "base_packs": 602, "bank_cache_hits": 1378, "pipeline_evaluations": 1552, "operations": {"transform_fits": 3739, "coefficient_fits": 4336, "linear_solves": 3176, "svd_calls": 2320}, "elapsed_seconds": 20.108999999938533, "peak_working_set_bytes": 49692672}
2. 审查要求删fixed_half_mixture才算ordinary。但原冻结安排是比较简单混合，固定50/50(candidate+selecteddirect)全程计入最强替代基线。这是预先选择的更严格gate，不是数据泄漏。rho0exact copy是同一程序所以merged，mixture是不同程序非同构。此时是否仍有必须排除的统计理由？不得因它更严而事后放松门槛。可以指出名称ordinary不精确，区别数学bug vs保守比较选择。
实际selected及final循环摘录：
        selected={}
        for item in scores:
            family=item['config']['family']
            if family not in selected or (item['dna_mae'],key(item['config'])) < (selected[family]['dna_mae'],key(selected[family]['config'])):
                selected[family]=item
        write(P/'SOURCE_FIXED_CONFIG_PREDICTIONS.json',predictions)
        write(P/'SOURCE_STATE_ERRORS.json',states)
        write(P/'SOURCE_SELECTION.json',dict(scores=scores,selected=selected,selection_exposed=True))
        final={};route_masks=None
        for family,item in selected.items():
            c=item['config'];alpha=c['alpha'];pack=bank.get(source,alpha)
            if family=='refit':
                pred=np.concatenate([ordinary_refit(data,source,j,alpha,c['weight'],pack['transforms'],ledger) for j in dev])
                ledger['pipeline_evaluations']+=len(dev)
            else:
                h,target=training_history(data,bank,source,alpha)
                q=histories(data,dev,[select_record(pack,j) for j in dev])
                pred,extra=feedback_fit_predict(h,target,q,c,ledger)
                if family=='rho_0':route_masks={k:v.tolist() for k,v in extra['masks'].items()}
                ledger['pipeline_evaluations']+=1
            assert np.isfinite(pred).all();final[family]=pred.tolist()
        final['fixed_half_mixture']=(.5*np.array(final['rho_0'])+.5*np.array(final['direct'])).tolist()

允许明确反对root，但须给可复现事实。其余候选不具独特算法新颖性、单N和开发暴露等局限保持。完整smoke不是实证性能证据，仅数值程序和计数。
