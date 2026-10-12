"""Export the frozen final NEW_D1 maps without fitting, rotation or interpolation."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json
import numpy as np

SAMPLES=('red','green','yellow','blue')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def equal(a,b):return np.array_equal(a,b,equal_nan=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-run',type=Path,required=True)
    ap.add_argument('--package-dir',type=Path,required=True);ap.add_argument('--limits-from',type=Path,required=True)
    args=ap.parse_args();run=args.source_run.resolve();out=args.package_dir.resolve()
    (out/'data').mkdir(parents=True,exist_ok=True);(out/'provenance').mkdir(exist_ok=True)
    oldlimits=json.loads(args.limits_from.read_text(encoding='utf-8'));limits={};sources=[];checks=[]
    for sample in SAMPLES:
        source=run/'maps'/f'{sample}_550.npz';sourcehash=sha(source)
        with np.load(source,allow_pickle=False) as f:
            vals={'theta_deg':f['theta_deg'],'phi_deg':f['phi_deg'],'reconstruction':f['Bprocessed'],
              'reference':f['G'],'difference':f['Bprocessed']-f['G'],'comparison_mask':f['D1'],
              'source_display_mask':f['display_mask'],'original_Dp':f['D0'],'D1':f['D1'],
              'filled':f['filled_mask'],'replaced':f['replaced_mask'],
              'protected_internal':f['protected_internal'],'protected_external':f['protected_external']}
        shape=(len(vals['theta_deg']),len(vals['phi_deg']));n=int(np.prod(shape));mask=vals['comparison_mask']
        assert equal(mask,vals['source_display_mask']&np.isfinite(vals['reconstruction'])&np.isfinite(vals['reference']))
        assert vals['reconstruction'].dtype==vals['reference'].dtype==np.dtype('float64')
        npzpath=out/'data'/f'{sample}_550.npz';np.savez_compressed(npzpath,**vals)
        with np.load(npzpath,allow_pickle=False) as z:
            assert all(z[k].dtype==a.dtype and equal(z[k],a) for k,a in vals.items())
        header=['theta_index','phi_index','theta_deg','phi_deg','reconstruction_sr_inv','reference_sr_inv','difference_sr_inv',
          'comparison_valid','source_display_valid','original_Dp','D1','filled','replaced','protected_internal','protected_external']
        maskkeys=['comparison_mask','source_display_mask','original_Dp','D1','filled','replaced','protected_internal','protected_external']
        tab=np.empty((n,len(header)),dtype=np.float64)
        ii,jj=np.indices(shape);tab[:,0]=ii.ravel();tab[:,1]=jj.ravel()
        tab[:,2]=np.repeat(vals['theta_deg'],shape[1]);tab[:,3]=np.tile(vals['phi_deg'],shape[0])
        for j,k in enumerate(['reconstruction','reference','difference']+maskkeys,4):tab[:,j]=vals[k].ravel()
        csvpath=out/'data'/f'{sample}_550_grid.csv.gz'
        with gzip.open(csvpath,'wt',encoding='utf-8',newline='') as f:
            np.savetxt(f,tab,delimiter=',',header=','.join(header),comments='',fmt=['%d','%d']+['%.17g']*5+['%d']*8)
        with gzip.open(csvpath,'rt',encoding='utf-8') as f:back=np.loadtxt(f,delimiter=',',skiprows=1)
        assert equal(tab,back)
        difference_limit=float(np.percentile(abs(vals['difference'][mask]),99)) or .001
        limits[sample]={'bsdf_min':oldlimits[sample]['bsdf_min'],'bsdf_max':oldlimits[sample]['bsdf_max'],
          'difference_min':-difference_limit,'difference_max':difference_limit,
          'difference_rule':'99th percentile of absolute difference on final NEW_D1 comparison_mask, symmetric'}
        assert sha(source)==sourcehash
        sources.append({'case_id':sample+'_550','series':'NEW_D1','path':str(source),'sha256':sourcehash,
          'reconstruction_field':'Bprocessed','reference_field':'G','comparison_mask_field':'D1',
          'difference_definition':'Bprocessed-G','shape':list(shape),'dtype':str(vals['reconstruction'].dtype)})
        checks.append({'case_id':sample+'_550','comparison_cells':int(mask.sum()),'full_grid_cells':n,
          'all_NPZ_fields_dtype_and_values_exact':True,'all_CSV_cells_roundtrip_exact':True,
          'NPZ_sha256':sha(npzpath),'CSV_sha256':sha(csvpath)})
        print(sample+': frozen final maps exported; every NPZ field and CSV cell exact',flush=True)
        del back,tab,vals,ii,jj
    for name in ['integrals_64cases.csv','aggregate_summary.csv']:
        sources.append({'path':str(run/name),'sha256':sha(run/name),'series':'NEW_D1'})
    (out/'provenance/source_manifest.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    (out/'data/color_limits.json').write_text(json.dumps(limits,indent=2),encoding='utf-8')
    (out/'provenance/field_mapping.json').write_text(json.dumps({'series':'NEW_D1','source_run':str(run),
      'fields':{'reconstruction':'Bprocessed','reference':'G','difference':'Bprocessed-G','comparison_mask':'D1',
        'source_display_mask':'display_mask','original_Dp':'D0','D1':'D1','filled':'filled_mask','replaced':'replaced_mask',
        'protected_internal':'protected_internal','protected_external':'protected_external','theta_deg':'theta_deg','phi_deg':'phi_deg'},
      'axes_and_saved_dtypes_preserved':True,'new_fitting_or_interpolation':False},indent=2),encoding='utf-8')
    (out/'provenance/exported_array_identity.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')

if __name__=='__main__':main()
