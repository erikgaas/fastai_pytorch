
        #################################################
        ### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
        #################################################
        # file to edit: dev_nb/006_carvana.ipynb

from nb_005 import *

class ImageMask(Image):
    def lighting(self, func, *args, **kwargs): return self

    def refresh(self):
        self.sample_kwargs['mode'] = 'nearest'
        return super().refresh()

def open_mask(fn):
    return ImageMask(pil2tensor(PIL.Image.open(fn)).float())

# Same as `show_image`, but renamed with _ prefix
def _show_image(img, ax=None, figsize=(3,3), hide_axis=True, cmap='binary', alpha=None):
    if ax is None: fig,ax = plt.subplots(figsize=figsize)
    ax.imshow(image2np(img), cmap=cmap, alpha=alpha)
    if hide_axis: ax.axis('off')
    return ax

def show_image(x, y=None, ax=None, figsize=(3,3), alpha=0.5, hide_axis=True, cmap='viridis'):
    ax1 = _show_image(x, ax=ax, hide_axis=hide_axis, cmap=cmap)
    if y is not None: _show_image(y, ax=ax1, alpha=alpha, hide_axis=hide_axis, cmap=cmap)
    if hide_axis: ax1.axis('off')

def _show(self, ax=None, y=None, **kwargs):
    if y is not None: y=y.data
    return show_image(self.data, ax=ax, y=y, **kwargs)

Image.show = _show

class DatasetTfm(Dataset):
    def __init__(self, ds:Dataset, tfms:Collection[Callable]=None, tfm_y:bool=False, **kwargs):
        self.ds,self.tfms,self.tfm_y,self.x_kwargs = ds,tfms,tfm_y,kwargs
        self.y_kwargs = {**self.x_kwargs, 'do_resolve':False} # don't reset random vars

    def __len__(self): return len(self.ds)

    def __getitem__(self,idx):
        x,y = self.ds[idx]

        x = apply_tfms(self.tfms, x, **self.x_kwargs)
        if self.tfm_y: y = apply_tfms(self.tfms, y, **self.y_kwargs)
        return x, y

    def __getattr__(self,k): return getattr(self.ds, k)

import nb_002b,nb_005
nb_002b.DatasetTfm = DatasetTfm
nb_005.DatasetTfm  = DatasetTfm

class MatchedFilesDataset(DatasetBase):
    def __init__(self, x:Collection[Path], y:Collection[Path]):
        assert len(x)==len(y)
        self.x,self.y = np.array(x),np.array(y)

    def __getitem__(self, i):
        return open_image(self.x[i]), open_mask(self.y[i])

def split_arrs(idxs, *a):
    mask = np.zeros(len(a[0]),dtype=bool)
    mask[np.array(idxs)] = True
    return [(o[mask],o[~mask]) for o in map(np.array, a)]

def normalize_batch(b, mean, std, do_y=False):
    x,y = b
    x = normalize(x,mean,std)
    if do_y: y = normalize(y,mean,std)
    return x,y

def normalize_funcs(mean, std, do_y=False, device=None):
    if device is None: device=default_device
    return (partial(normalize_batch, mean=mean.to(device),std=std.to(device), do_y=do_y),
            partial(denormalize,     mean=mean,           std=std))

def show_xy_images(x,y,rows,figsize=(9,9)):
    fig, axs = plt.subplots(rows,rows,figsize=figsize)
    for i, ax in enumerate(axs.flatten()): show_image(x[i], y=y[i], ax=ax)
    plt.tight_layout()

class Debugger(nn.Module):
    def forward(self,x):
        set_trace()
        return x

class StdUpsample(nn.Module):
    def __init__(self, nin, nout):
        super().__init__()
        self.conv = conv2d_trans(nin, nout)
        self.bn = nn.BatchNorm2d(nout)

    def forward(self, x):
        return self.bn(F.relu(self.conv(x)))

def std_upsample_head(*nfs):
    return nn.Sequential(
        nn.ReLU(),
        *(StdUpsample(nfs[i],nfs[i+1]) for i in range(4)),
        conv2d_trans(nfs[-1], 1)
    )

def dice(pred, targs):
    pred = (pred>0).float()
    return 2. * (pred*targs).sum() / (pred+targs).sum()