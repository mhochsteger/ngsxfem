#define FILE_DIFFOPDT_CPP
#include "diffopDt.hpp"
#include <diffop_impl.hpp>
#include "SpaceTimeFE.hpp"


namespace ngfem
{

  template <int SpaceD>
    template<typename FEL, typename MIP, typename MAT>
  void DiffOpDt<SpaceD>::GenerateMatrix (const FEL & bfel, const MIP & mip,
                                             MAT & mat, LocalHeap & lh)
  {
      IntegrationPoint ip(mip.IP());
      mat = 0.0;

      const SpaceTimeFE<SpaceD>* scafed = dynamic_cast<const SpaceTimeFE<SpaceD> * > (& bfel);
      FlatVector<> dtshape (scafed->GetNDof(),lh);
      scafed->CalcDtShape(ip,dtshape);
      mat.Row(0) = dtshape;
    }

  template class T_DifferentialOperator<DiffOpDt<2>>;
  template class T_DifferentialOperator<DiffOpDt<3>>;

  template <int SpaceD, int D>
  template <typename FEL, typename MIP, typename MAT>
  void DiffOpDtVec<SpaceD, D>::GenerateMatrix (const FEL & bfel, const MIP & mip,
                                             MAT & mat, LocalHeap & lh)
  {
      IntegrationPoint ip(mip.IP());
      mat = 0.0;

      const SpaceTimeFE<SpaceD>& scafed = dynamic_cast<const SpaceTimeFE<SpaceD>& > (bfel);
      FlatVector<> dtshape (scafed.GetNDof(),lh);
      scafed.CalcDtShape(ip,dtshape);
      for (int j = 0; j < D; j++)
        for (int k = 0; k < dtshape.Size(); k++)
            mat(j,k*D+j) = dtshape(k);
    }

  template class T_DifferentialOperator<DiffOpDtVec<2, 1>>;
  template class T_DifferentialOperator<DiffOpDtVec<2, 2>>;
  template class T_DifferentialOperator<DiffOpDtVec<2, 3>>;

  template class T_DifferentialOperator<DiffOpDtVec<3, 1>>;
  template class T_DifferentialOperator<DiffOpDtVec<3, 2>>;
  template class T_DifferentialOperator<DiffOpDtVec<3, 3>>;

  template <int SpaceD, int time>
  template <typename FEL, typename MIP, typename MAT>
  void DiffOpFixt<SpaceD, time>::GenerateMatrix (const FEL & bfel, const MIP & mip,
                                             MAT & mat, LocalHeap & lh)
  {

      IntegrationPoint ip(mip.IP()(0),mip.IP()(1), mip.IP()(2), time);
      ip.SetPrecomputedGeometry(true);
      mat = 0.0;
      const SpaceTimeFE<SpaceD>& scafed = dynamic_cast<const SpaceTimeFE<SpaceD> & > (bfel);

      FlatVector<> shape (scafed.GetNDof(),lh);
      scafed.CalcShape(ip,shape);
      mat.Row(0) = shape;
   }

  template class T_DifferentialOperator<DiffOpFixt<2, 0>>;
  template class T_DifferentialOperator<DiffOpFixt<2, 1>>;

  template class T_DifferentialOperator<DiffOpFixt<3, 0>>;
  template class T_DifferentialOperator<DiffOpFixt<3, 1>>;

  template<int SpaceD>
  void DiffOpFixAnyTime<SpaceD> ::
  CalcMatrix (const FiniteElement & bfel,
              const BaseMappedIntegrationPoint & bmip,
              SliceMatrix<double,ColMajor> mat,
              LocalHeap & lh) const
  {

      mat = 0.0;
      const MappedIntegrationPoint<DIM_ELEMENT,DIM_SPACE> & mip =
      static_cast<const MappedIntegrationPoint<DIM_ELEMENT,DIM_SPACE>&> (bmip);

      IntegrationPoint ip(mip.IP()(0),mip.IP()(1),mip.IP()(2), time);
      ip.SetPrecomputedGeometry(true);

      const SpaceTimeFE<SpaceD>& scafed = dynamic_cast<const SpaceTimeFE<SpaceD> &> (bfel);

      FlatVector<> shape (scafed.GetNDof(),lh);
      scafed.CalcShape(ip,shape);
      mat.Row(0) = shape;
  }

  template<int SpaceD>
  void DiffOpFixAnyTime<SpaceD> ::
  ApplyTrans (const FiniteElement & fel,
              const BaseMappedIntegrationPoint & mip,
              FlatVector<double> flux,
              FlatVector<double> x,
              LocalHeap & lh) const
  {
    HeapReset hr(lh);
    FlatMatrix<double,ColMajor> mat(Dim(), x.Size(), lh);
    CalcMatrix (fel, mip, mat, lh);
    x = Trans(mat) * flux;
  }

  template class DiffOpFixAnyTime<2>;
  template class DiffOpFixAnyTime<3>;

}


